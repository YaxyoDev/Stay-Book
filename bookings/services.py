from decimal import Decimal
from datetime import date
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

from hotels.models import Room
from .models import Booking, BookingStatus, BookingStatusLog


def get_overlapping_bookings_query(check_in: date, check_out: date):
    """
    Overlap formula according to specification:
    existing.check_in < new_check_out AND existing.check_out > new_check_in
    Statuses that block a room: PENDING, CONFIRMED
    """
    return Q(
        check_in__lt=check_out,
        check_out__gt=check_in,
        status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]
    )


def is_room_available(room_id: int, check_in: date, check_out: date, exclude_booking_id=None) -> bool:
    """
    Check if a room is available for [check_in, check_out).
    """
    query = get_overlapping_bookings_query(check_in, check_out) & Q(room_id=room_id)
    if exclude_booking_id:
        query &= ~Q(id=exclude_booking_id)
    return not Booking.objects.filter(query).exists()


def calculate_total_price(price_per_night: Decimal, check_in: date, check_out: date) -> tuple[int, Decimal]:
    """
    Calculate nights and total price on server side.
    Client-sent prices are NEVER trusted.
    """
    if check_in >= check_out:
        raise ValidationError("Chiqish sanasi kirish sanasidan keyin bo‘lishi kerak.")
    nights = (check_out - check_in).days
    if nights < 1:
        raise ValidationError("Minimal bron muddati 1 kecha.")
    if nights > 30:
        raise ValidationError("Maksimal bron muddati 30 kecha.")
    total = price_per_night * Decimal(nights)
    return nights, total


def create_booking_atomic(
    user,
    room_id: int,
    check_in: date,
    check_out: date,
    adults: int,
    children: int,
    guest_name: str,
    guest_phone: str,
    special_requests: str = "",
    actor=None
) -> Booking:
    """
    Thread-safe & race-condition-free booking creation:
    1. Runs inside transaction.atomic()
    2. Locks the Room row using select_for_update()
    3. Re-checks date availability
    4. Validates capacity and hotel status
    5. Calculates server-side price snapshot
    6. Creates Booking & BookingStatusLog
    """
    today = timezone.localdate()
    if check_in < today:
        raise ValidationError("O‘tgan sanalarni bron qilib bo‘lmaydi.")
    if check_in >= check_out:
        raise ValidationError("Chiqish sanasi kirish sanasidan keyin bo‘lishi kerak.")

    with transaction.atomic():
        # Concurrency Lock: Lock the room row so concurrent requests queue up
        try:
            room = Room.objects.select_for_update().get(id=room_id)
        except Room.DoesNotExist:
            raise ValidationError("Tanlangan xona topilmadi.")

        if not room.is_active:
            raise ValidationError("Ushbu xona ayni paytda faol emas.")
        if not room.hotel.is_published:
            raise ValidationError("Ushbu mehmonxona ayni paytda faol emas.")

        # Capacity check
        total_guests = adults + children
        if adults > room.capacity_adults or total_guests > room.total_capacity:
            raise ValidationError(
                f"Mehmonlar soni xona sig‘imidan oshib ketdi. "
                f"Ushbu xona ko‘pi bilan {room.capacity_adults} nafar katta va "
                f"{room.capacity_children} nafar bola uchun mo‘ljallangan."
            )

        # Overlapping check under lock
        overlapping = Booking.objects.filter(
            get_overlapping_bookings_query(check_in, check_out),
            room=room
        ).exists()

        if overlapping:
            raise ValidationError(
                "Kechirasiz, tanlangan sanalarda bu xona allaqachon band qilingan. "
                "Iltimos, boshqa sanalarni yoki boshqa xonani tanlang."
            )

        # Calculate exact price snapshot
        nights, total_price = calculate_total_price(room.price_per_night, check_in, check_out)

        booking = Booking.objects.create(
            user=user,
            room=room,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children,
            guest_name=guest_name.strip(),
            guest_phone=guest_phone.strip(),
            nightly_price_snapshot=room.price_per_night,
            total_price=total_price,
            status=BookingStatus.PENDING,
            special_requests=special_requests.strip()
        )

        BookingStatusLog.objects.create(
            booking=booking,
            old_status='',
            new_status=BookingStatus.PENDING,
            actor=actor or user,
            note="Bron mijoz tomonidan yaratildi."
        )

        return booking


def cancel_booking(booking: Booking, actor, note: str = "") -> Booking:
    """
    Cancel an existing booking and log the status transition.
    """
    if not booking.can_cancel:
        raise ValidationError("Ushbu bronni bekor qilib bo‘lmaydi.")

    with transaction.atomic():
        old_status = booking.status
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancelled_at', 'updated_at'])

        BookingStatusLog.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=BookingStatus.CANCELLED,
            actor=actor,
            note=note or "Bron bekor qilindi."
        )

    return booking


def update_booking_status(booking: Booking, new_status: str, actor, note: str = "") -> Booking:
    """
    Manager/Admin updates booking status (e.g. CONFIRMED, REJECTED, COMPLETED).
    """
    if new_status not in BookingStatus.values:
        raise ValidationError("Noto‘g‘ri bron holati.")

    with transaction.atomic():
        old_status = booking.status
        if old_status == new_status:
            return booking

        booking.status = new_status
        if new_status == BookingStatus.CANCELLED:
            booking.cancelled_at = timezone.now()
            booking.save(update_fields=['status', 'cancelled_at', 'updated_at'])
        else:
            booking.save(update_fields=['status', 'updated_at'])

        BookingStatusLog.objects.create(
            booking=booking,
            old_status=old_status,
            new_status=new_status,
            actor=actor,
            note=note
        )

    return booking
