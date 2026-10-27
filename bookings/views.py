from datetime import datetime, date
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

from hotels.models import Room
from .models import Booking, BookingStatus, BookingStatusLog
from .forms import BookingCreateForm
from .services import create_booking_atomic, cancel_booking, update_booking_status, calculate_total_price


def parse_date(date_str: str) -> date | None:
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    return None


@login_required
def booking_create_view(request, room_id):
    """
    Booking creation view: validates capacity, locks room with select_for_update() inside transaction,
    creates booking and logs status change.
    """
    room = get_object_or_404(
        Room.objects.filter(is_active=True, hotel__is_published=True).select_related('hotel'),
        pk=room_id
    )

    # Initial data from GET params
    check_in_init = parse_date(request.GET.get('check_in')) or timezone.localdate()
    check_out_init = parse_date(request.GET.get('check_out')) or (timezone.localdate() + timezone.timedelta(days=1))
    adults_init = int(request.GET.get('adults', 1)) if request.GET.get('adults', '').isdigit() else 1
    children_init = int(request.GET.get('children', 0)) if request.GET.get('children', '').isdigit() else 0

    guest_name_init = request.user.get_full_name() or request.user.username
    guest_phone_init = request.user.phone

    if request.method == 'POST':
        form = BookingCreateForm(request.POST)
        if form.is_valid():
            try:
                booking = create_booking_atomic(
                    user=request.user,
                    room_id=room.id,
                    check_in=form.cleaned_data['check_in'],
                    check_out=form.cleaned_data['check_out'],
                    adults=form.cleaned_data['adults'],
                    children=form.cleaned_data['children'],
                    guest_name=form.cleaned_data['guest_name'],
                    guest_phone=form.cleaned_data['guest_phone'],
                    special_requests=form.cleaned_data.get('special_requests', ''),
                    actor=request.user
                )
                messages.success(request, "Broningiz muvaffaqiyatli qabul qilindi! To‘lov mehmonxonaga yetib borganda amalga oshiriladi.")
                return redirect('bookings:detail', pk=booking.pk)
            except ValidationError as e:
                messages.error(request, e.message if hasattr(e, 'message') else str(e))
            except Exception as e:
                messages.error(request, f"Bron yaratishda kutilmagan xatolik yuz berdi: {str(e)}")
        else:
            messages.error(request, "Iltimos, formadagi xatoliklarni to‘g‘rilang.")
    else:
        form = BookingCreateForm(initial={
            'check_in': check_in_init,
            'check_out': check_out_init,
            'adults': min(adults_init, room.capacity_adults),
            'children': children_init,
            'guest_name': guest_name_init,
            'guest_phone': guest_phone_init,
        })

    # Estimate price for display
    nights = max(1, (check_out_init - check_in_init).days) if check_out_init > check_in_init else 1
    estimated_total = room.price_per_night * Decimal(nights)

    context = {
        'room': room,
        'hotel': room.hotel,
        'form': form,
        'nights': nights,
        'estimated_total': estimated_total,
    }
    return render(request, 'bookings/booking_create.html', context)


@login_required
def booking_list_view(request):
    """
    Customer dashboard / My Bookings matching stitch_task_and_reading_tracker/shaxsiy_kabinet_bronlarim/code.html
    """
    user = request.user
    bookings_qs = user.bookings.select_related('room__hotel').prefetch_related('room__images', 'room__hotel__images').order_by('-created_at')

    # Status tab filter
    tab = request.GET.get('tab', 'all')
    if tab == 'active':
        bookings = bookings_qs.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED])
    elif tab == 'completed':
        bookings = bookings_qs.filter(status=BookingStatus.COMPLETED)
    elif tab == 'cancelled':
        bookings = bookings_qs.filter(status__in=[BookingStatus.CANCELLED, BookingStatus.REJECTED])
    else:
        bookings = bookings_qs

    # Counts
    active_count = bookings_qs.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]).count()
    completed_count = bookings_qs.filter(status=BookingStatus.COMPLETED).count()
    cancelled_count = bookings_qs.filter(status__in=[BookingStatus.CANCELLED, BookingStatus.REJECTED]).count()

    context = {
        'bookings': bookings,
        'current_tab': tab,
        'active_count': active_count,
        'completed_count': completed_count,
        'cancelled_count': cancelled_count,
        'total_count': bookings_qs.count(),
    }
    return render(request, 'bookings/booking_list.html', context)


@login_required
def booking_detail_view(request, pk):
    """
    Booking confirmation voucher & detail view.
    Access is restricted to booking owner, room hotel manager, or superuser.
    """
    booking = get_object_or_404(
        Booking.objects.select_related('room__hotel__manager', 'user').prefetch_related('status_logs__actor', 'room__images', 'room__hotel__images'),
        pk=pk
    )

    # Permission check: owner or hotel manager or superuser
    is_owner = (booking.user == request.user)
    is_manager = (booking.room.hotel.manager == request.user or request.user.is_superuser)

    if not is_owner and not is_manager:
        raise PermissionDenied("Siz ushbu bron ma'lumotlarini ko‘rish huquqiga ega emassiz.")

    has_reviewed = hasattr(booking, 'review')

    context = {
        'booking': booking,
        'hotel': booking.room.hotel,
        'room': booking.room,
        'is_owner': is_owner,
        'is_manager': is_manager,
        'has_reviewed': has_reviewed,
        'status_logs': booking.status_logs.all(),
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required
@require_POST
def booking_cancel_view(request, pk):
    """
    Customer cancels their own booking.
    """
    booking = get_object_or_404(Booking, pk=pk)

    if booking.user != request.user and not request.user.is_superuser:
        raise PermissionDenied("Siz faqat o‘zingizga tegishli bronni bekor qilishingiz mumkin.")

    if not booking.can_cancel:
        messages.error(request, "Ushbu bronni bekor qilish muddatidan o‘tgan yoki holati bekor qilishga ruxsat bermaydi.")
        return redirect('bookings:detail', pk=booking.pk)

    try:
        cancel_booking(booking, actor=request.user, note="Mijoz o‘z kabinetidan bekor qildi.")
        messages.success(request, "Broningiz muvaffaqiyatli bekor qilindi.")
    except ValidationError as e:
        messages.error(request, e.message if hasattr(e, 'message') else str(e))

    return redirect('bookings:detail', pk=booking.pk)


@login_required
@require_POST
def booking_status_update_view(request, pk):
    """
    Hotel Manager updates booking status (CONFIRMED, REJECTED, COMPLETED).
    """
    booking = get_object_or_404(Booking.objects.select_related('room__hotel__manager'), pk=pk)

    # Ownership check: manager can only manage their own hotel's bookings
    if booking.room.hotel.manager != request.user and not request.user.is_superuser:
        raise PermissionDenied("Siz faqat o‘z mehmonxonangizga tegishli bronlar holatini o‘zgartira olasiz.")

    new_status = request.POST.get('status')
    note = request.POST.get('note', '').strip()

    try:
        update_booking_status(booking, new_status, actor=request.user, note=note)
        messages.success(request, f"Bron holati '{booking.get_status_display()}' ga o‘zgartirildi.")
    except ValidationError as e:
        messages.error(request, str(e))

    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('bookings:detail', pk=booking.pk)
