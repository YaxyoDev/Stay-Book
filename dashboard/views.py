from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from accounts.permissions import manager_required
from hotels.models import Hotel, Room, RoomImage
from bookings.models import Booking, BookingStatus
from bookings.services import update_booking_status, get_overlapping_bookings_query
from .forms import HotelForm, RoomForm, RoomImageForm


@manager_required
def dashboard_overview(request):
    """
    Hotel Manager Dashboard Overview with KPI metrics and recent bookings.
    Strictly isolated to manager's own hotels.
    """
    user = request.user
    today = timezone.localdate()

    if user.is_superuser:
        hotels_qs = Hotel.objects.all()
    else:
        hotels_qs = Hotel.objects.filter(manager=user)

    hotel_ids = list(hotels_qs.values_list('id', flat=True))
    bookings_qs = Booking.objects.filter(room__hotel_id__in=hotel_ids).select_related('room__hotel', 'user')

    # 1. KPI Cards
    today_checkins_count = bookings_qs.filter(check_in=today, status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]).count()
    pending_bookings_count = bookings_qs.filter(status=BookingStatus.PENDING).count()
    total_bookings_count = bookings_qs.count()

    # Active occupied rooms today
    occupied_rooms_count = bookings_qs.filter(
        get_overlapping_bookings_query(today, today + timezone.timedelta(days=1))
    ).values('room_id').distinct().count()

    # Total pipeline booking value (bron qiymatlari)
    total_revenue_stats = bookings_qs.filter(
        status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    # Recent 6 bookings
    recent_bookings = bookings_qs.order_by('-created_at')[:6]

    context = {
        'hotels': hotels_qs,
        'today_checkins_count': today_checkins_count,
        'pending_bookings_count': pending_bookings_count,
        'total_bookings_count': total_bookings_count,
        'occupied_rooms_count': occupied_rooms_count,
        'total_revenue_stats': total_revenue_stats,
        'recent_bookings': recent_bookings,
        'today': today,
    }
    return render(request, 'dashboard/overview.html', context)


@manager_required
def dashboard_hotels(request):
    """
    Manage manager's own hotels (List and Edit).
    """
    user = request.user
    if user.is_superuser:
        hotels = Hotel.objects.all().prefetch_related('rooms', 'images')
    else:
        hotels = Hotel.objects.filter(manager=user).prefetch_related('rooms', 'images')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_hotel':
            form = HotelForm(request.POST)
            if form.is_valid():
                hotel = form.save(commit=False)
                hotel.manager = user
                hotel.save()
                form.save_m2m()
                messages.success(request, f"'{hotel.name}' mehmonxonasi muvaffaqiyatli yaratildi.")
                return redirect('dashboard:hotels')
            else:
                messages.error(request, "Mehmonxona ma'lumotlarini saqlashda xatolik yuz berdi.")
        else:
            form = HotelForm()
    else:
        form = HotelForm()

    context = {
        'hotels': hotels,
        'form': form,
    }
    return render(request, 'dashboard/hotels.html', context)


@manager_required
def dashboard_rooms(request):
    """
    Manage manager's rooms (List, Add, Edit, Toggle Active).
    """
    user = request.user
    if user.is_superuser:
        hotels_qs = Hotel.objects.all()
    else:
        hotels_qs = Hotel.objects.filter(manager=user)

    hotel_ids = list(hotels_qs.values_list('id', flat=True))
    rooms = Room.objects.filter(hotel_id__in=hotel_ids).select_related('hotel').prefetch_related('images').order_by('hotel__name', 'number')

    hotel_filter = request.GET.get('hotel')
    if hotel_filter and hotel_filter.isdigit():
        rooms = rooms.filter(hotel_id=int(hotel_filter))

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_room':
            form = RoomForm(request.POST, user=user)
            if form.is_valid():
                room = form.save()
                messages.success(request, f"№ {room.number} xona muvaffaqiyatli qo‘shildi.")
                return redirect('dashboard:rooms')
            else:
                messages.error(request, "Xona yaratishda xatolik yuz berdi.")
        elif action == 'toggle_active':
            room_id = request.POST.get('room_id')
            room = get_object_or_404(Room, id=room_id, hotel_id__in=hotel_ids)
            room.is_active = not room.is_active
            room.save(update_fields=['is_active'])
            status_str = "faollashtirildi" if room.is_active else "faolsizlantirildi"
            messages.success(request, f"№ {room.number} xona holati {status_str}.")
            return redirect('dashboard:rooms')
        else:
            form = RoomForm(user=user)
    else:
        form = RoomForm(user=user)

    context = {
        'rooms': rooms,
        'hotels': hotels_qs,
        'selected_hotel': int(hotel_filter) if hotel_filter and hotel_filter.isdigit() else None,
        'form': form,
    }
    return render(request, 'dashboard/rooms.html', context)


@manager_required
def dashboard_bookings(request):
    """
    Manager's incoming bookings table with filtering, search, and status confirmation workflow.
    """
    user = request.user
    if user.is_superuser:
        hotels_qs = Hotel.objects.all()
    else:
        hotels_qs = Hotel.objects.filter(manager=user)

    hotel_ids = list(hotels_qs.values_list('id', flat=True))
    bookings_qs = Booking.objects.filter(room__hotel_id__in=hotel_ids).select_related('room__hotel', 'user').order_by('-created_at')

    # Filters
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    hotel_filter = request.GET.get('hotel', '').strip()

    if q:
        bookings_qs = bookings_qs.filter(
            Q(guest_name__icontains=q) |
            Q(guest_phone__icontains=q) |
            Q(id__icontains=q) |
            Q(room__number__icontains=q)
        )

    if status_filter:
        bookings_qs = bookings_qs.filter(status=status_filter)

    if hotel_filter and hotel_filter.isdigit():
        bookings_qs = bookings_qs.filter(room__hotel_id=int(hotel_filter))

    context = {
        'bookings': bookings_qs,
        'hotels': hotels_qs,
        'status_choices': BookingStatus.choices,
        'current_q': q,
        'current_status': status_filter,
        'current_hotel': int(hotel_filter) if hotel_filter and hotel_filter.isdigit() else None,
    }
    return render(request, 'dashboard/bookings.html', context)
