from datetime import datetime, date
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Min, Avg, Count, F
from django.utils import timezone
from django.contrib import messages

from .models import Hotel, Room, Amenity
from bookings.models import Booking, BookingStatus
from bookings.services import get_overlapping_bookings_query, calculate_total_price


def parse_date_param(date_str: str) -> date | None:
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y.%m.%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def home_view(request):
    """
    Landing page matching stitch_task_and_reading_tracker/staybook_bosh_sahifa/code.html
    """
    featured_hotels = (
        Hotel.objects.filter(is_published=True)
        .prefetch_related('images', 'amenities', 'rooms', 'reviews')
        .annotate(
            min_room_price=Min('rooms__price_per_night', filter=Q(rooms__is_active=True)),
            avg_review_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
            review_total=Count('reviews', filter=Q(reviews__is_visible=True), distinct=True)
        )
        .order_by('-stars', '-created_at')[:6]
    )

    # City counts
    cities_data = [
        {'name': 'Toshkent', 'count': Hotel.objects.filter(city__iexact='Toshkent', is_published=True).count(), 'desc': 'Zamonaviy poytaxt ritmi va qulaylik', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuCk4fpQO-F4CwlRbeJdWHy57SqwsVmuLodcI31-a2-2u6z8Dpd9qe8VsEHNnwFNKWPvAhsUFUSxnnxRrF2gssfSwnhclvRfYS8A1ckoICKMYbjM5p42q715Y-qbPl5VGiLTmBOoVL9KEIcV-z7dx0lSYOv3JpcfK0wh5PkjOrK6iPXvHgwuPt19yowNSgdtC2IshxWoPvj_b4s8-0q87cHcPniE5WjkJ30MCbFj7XnjPVUQFWtidPxMDA'},
        {'name': 'Samarqand', 'count': Hotel.objects.filter(city__iexact='Samarqand', is_published=True).count(), 'desc': 'Afsonaviy Registon va moviy gumbazlar', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDnM9wU6YeT1_06R4Lhwpwz6PYtcaLKBuw1T2J2D_vmTnPromdeQDnLgzI0t8CFbIYEvtRFMYIauog8eR6daUQuufvLTkaFR3K9Wn-43aurx0saKG80BbPJXwXs9ZBxktAw9cF63Oqgu3TYMSZDmj_WivPxp_0gn13R4gRVZhzGm6JUob5MPomCrZVcbWlCaQ8AaBZguC_Ng8jX1cDjLD_0QnR6vcbZ43N4MH-lKxRgcCBAP62XBZnukg'},
        {'name': 'Buxoro', 'count': Hotel.objects.filter(city__iexact='Buxoro', is_published=True).count(), 'desc': 'Eski shahar va qadimiy karvonsaroylar', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAGjcOSmSq5KN_kJ5ToLerY6fmSqiggDvkClhbr1S7QutqmYWQrKDhrMTwXGlt_aiXdlJlNDqb_P8nFUsLELiNmVK9QqSKpTqrwS-IPKToBaecdWLQBnolSjvgczreSKM9qtqEER1U7jrxph179DJT41UstrRnjd31tNYYFLx5-1ggyTAXyxfQWEFN2KqFYanUMcww13nQyojnol8khZ5b0WJpVr_YcXVHv5ypwweEAWROvhVmTuUrp-A'},
        {'name': 'Xiva', 'count': Hotel.objects.filter(city__iexact='Xiva', is_published=True).count(), 'desc': 'Ichan Qal\'a — ochiq osmon ostidagi muzey', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuChnOhHfgUqtLv9pANshhE7fxcVZ9dwmR0PhVA12IfimD-NXP8UBVFuQfSDdkcM2Nfz0Zd-t0Bpi-2vEj1UfRTILqcCVBjMvFeBOnZivzliRkbgRCyHBIHJ5uBgu-NkDi7fkNshfw289AiR7PExFTVEEwMQCLUc1omsCWothkBO2i-7wSZdYVlmlPsMdqhoD-45MwK8uJp0sNxeVHMpa78J7rtRkaYBjmd9AAqnWZaIKOTcT3UORia29g'},
        {'name': 'Zomin', 'count': Hotel.objects.filter(city__iexact='Zomin', is_published=True).count(), 'desc': 'Go\'zal tog\' havosi va sokin tabiat bag\'ri', 'img': 'https://lh3.googleusercontent.com/aida-public/AB6AXuC3tgT8xQSD7btNIoYAJuP1KzolKWdfBl86XamGvToBponbadE95mSsar_iv7fJeJ5bTCkGvRAw4n5OUlNn2O0J268z9OQQKpkFXH6amDqCJlIFVyvvbX-Wwloz-FdZGor1QC-GOzyZvMKfHQw6U-nfcILpqOJHD9H70TH7ZmzW17NopGma5lS4GpMurGFDD53YpxpZgZPbYJSfC_zfeWrlnUjCVVDWXtsEgR47jdi3_fDlxIH64ngE3w'},
    ]

    context = {
        'featured_hotels': featured_hotels,
        'cities_data': cities_data,
        'today_str': timezone.localdate().isoformat(),
    }
    return render(request, 'hotels/home.html', context)


def hotel_list_view(request):
    """
    Hotel catalog with comprehensive search, filters, date availability, sorting, and pagination.
    Matching stitch_task_and_reading_tracker/staybook_mehmonxonalar_ro_yxati_va_qidiruv/code.html
    """
    queryset = Hotel.objects.filter(is_published=True).prefetch_related('images', 'amenities', 'rooms', 'reviews')

    # Query params
    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    stars_list = request.GET.getlist('stars')
    amenities_list = request.GET.getlist('amenity')
    sort_by = request.GET.get('sort', 'rating_desc')

    check_in_raw = request.GET.get('check_in', '').strip()
    check_out_raw = request.GET.get('check_out', '').strip()
    adults_raw = request.GET.get('adults', '1').strip()
    children_raw = request.GET.get('children', '0').strip()

    check_in = parse_date_param(check_in_raw)
    check_out = parse_date_param(check_out_raw)

    try:
        adults = max(1, int(adults_raw))
    except (ValueError, TypeError):
        adults = 1

    try:
        children = max(0, int(children_raw))
    except (ValueError, TypeError):
        children = 0

    # Date validation
    dates_valid = False
    if check_in_raw or check_out_raw:
        today = timezone.localdate()
        if not check_in or not check_out:
            messages.warning(request, "Iltimos, ham kirish, ham chiqish sanasini to‘liq tanlang.")
        elif check_in < today:
            messages.warning(request, "Kirish sanasi bugungi kundan oldin bo‘lishi mumkin emas.")
        elif check_in >= check_out:
            messages.warning(request, "Chiqish sanasi kirish sanasidan keyin bo‘lishi shart.")
        else:
            dates_valid = True

    # Text search
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(city__icontains=q) |
            Q(address__icontains=q)
        )

    # City filter
    if city:
        queryset = queryset.filter(city__iexact=city)

    # Stars filter
    if stars_list:
        try:
            stars_ints = [int(s) for s in stars_list if s.isdigit()]
            if stars_ints:
                queryset = queryset.filter(stars__in=stars_ints)
        except ValueError:
            pass

    # Amenities filter
    if amenities_list:
        for amen_id in amenities_list:
            if amen_id.isdigit():
                queryset = queryset.filter(amenities__id=int(amen_id))

    # Room-level availability filter
    room_filter = Q(rooms__is_active=True)
    if dates_valid:
        # Exclude rooms that have overlapping active bookings
        overlapping_rooms = Booking.objects.filter(
            get_overlapping_bookings_query(check_in, check_out)
        ).values_list('room_id', flat=True)

        room_filter &= ~Q(rooms__id__in=overlapping_rooms)
        room_filter &= Q(rooms__capacity_adults__gte=adults)
        total_guests = adults + children
        room_filter &= Q(rooms__capacity_adults__gte=adults)

    queryset = queryset.filter(room_filter).distinct()

    # Min/Max Price filter (filtered against hotel's active rooms)
    if min_price and min_price.isdigit():
        queryset = queryset.filter(rooms__price_per_night__gte=Decimal(min_price), rooms__is_active=True).distinct()
    if max_price and max_price.isdigit():
        queryset = queryset.filter(rooms__price_per_night__lte=Decimal(max_price), rooms__is_active=True).distinct()

    # Annotation for sorting
    queryset = queryset.annotate(
        min_room_price=Min('rooms__price_per_night', filter=Q(rooms__is_active=True)),
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_visible=True)),
        total_reviews=Count('reviews', filter=Q(reviews__is_visible=True), distinct=True)
    )

    # Sorting
    if sort_by == 'price_asc':
        queryset = queryset.order_by(F('min_room_price').asc(nulls_last=True))
    elif sort_by == 'price_desc':
        queryset = queryset.order_by(F('min_room_price').desc(nulls_last=True))
    elif sort_by == 'rating_desc':
        queryset = queryset.order_by(F('avg_rating').desc(nulls_last=True), '-stars')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by(F('avg_rating').desc(nulls_last=True), '-stars')

    # Pagination
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Clean query parameters for pagination links (excluding 'page')
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    extra_query = query_params.urlencode()

    all_amenities = Amenity.objects.all()
    available_cities = Hotel.objects.filter(is_published=True).values_list('city', flat=True).distinct().order_by('city')

    context = {
        'page_obj': page_obj,
        'total_hotels': paginator.count,
        'all_amenities': all_amenities,
        'available_cities': available_cities,
        'current_city': city,
        'current_q': q,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'selected_stars': stars_list,
        'selected_amenities': [int(a) for a in amenities_list if a.isdigit()],
        'sort_by': sort_by,
        'check_in': check_in.isoformat() if check_in else '',
        'check_out': check_out.isoformat() if check_out else '',
        'adults': adults,
        'children': children,
        'dates_valid': dates_valid,
        'extra_query': extra_query,
    }
    return render(request, 'hotels/hotel_list.html', context)


def hotel_detail_view(request, slug):
    """
    Hotel detail page matching stitch_task_and_reading_tracker/silk_road_grand_hotel_mehmonxona_haqida/code.html
    """
    hotel = get_object_or_404(
        Hotel.objects.filter(is_published=True)
        .prefetch_related('images', 'amenities', 'rooms__images', 'reviews__user'),
        slug=slug
    )

    check_in_raw = request.GET.get('check_in', '').strip()
    check_out_raw = request.GET.get('check_out', '').strip()
    adults_raw = request.GET.get('adults', '2').strip()
    children_raw = request.GET.get('children', '0').strip()

    check_in = parse_date_param(check_in_raw)
    check_out = parse_date_param(check_out_raw)

    try:
        adults = max(1, int(adults_raw))
    except (ValueError, TypeError):
        adults = 2

    try:
        children = max(0, int(children_raw))
    except (ValueError, TypeError):
        children = 0

    dates_valid = False
    nights = 0
    if check_in and check_out:
        today = timezone.localdate()
        if check_in >= today and check_out > check_in:
            dates_valid = True
            nights = (check_out - check_in).days

    # Load rooms and evaluate availability
    rooms = list(hotel.rooms.filter(is_active=True).prefetch_related('images'))
    booked_room_ids = set()

    if dates_valid:
        booked_room_ids = set(
            Booking.objects.filter(
                get_overlapping_bookings_query(check_in, check_out),
                room__hotel=hotel
            ).values_list('room_id', flat=True)
        )

    for room in rooms:
        if dates_valid:
            room.is_booked_for_dates = room.id in booked_room_ids
            room.is_capacity_fit = room.capacity_adults >= adults and room.total_capacity >= (adults + children)
            _, room.calc_total_price = calculate_total_price(room.price_per_night, check_in, check_out)
        else:
            room.is_booked_for_dates = False
            room.is_capacity_fit = True
            room.calc_total_price = room.price_per_night

    reviews = hotel.reviews.filter(is_visible=True).select_related('user')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None

    context = {
        'hotel': hotel,
        'rooms': rooms,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'reviews_count': reviews.count(),
        'check_in': check_in.isoformat() if check_in else '',
        'check_out': check_out.isoformat() if check_out else '',
        'adults': adults,
        'children': children,
        'dates_valid': dates_valid,
        'nights': nights,
    }
    return render(request, 'hotels/hotel_detail.html', context)


def room_detail_view(request, pk):
    """
    Room detail view.
    """
    room = get_object_or_404(
        Room.objects.filter(is_active=True, hotel__is_published=True).select_related('hotel').prefetch_related('images'),
        pk=pk
    )

    check_in_raw = request.GET.get('check_in', '').strip()
    check_out_raw = request.GET.get('check_out', '').strip()
    adults_raw = request.GET.get('adults', '2').strip()
    children_raw = request.GET.get('children', '0').strip()

    check_in = parse_date_param(check_in_raw)
    check_out = parse_date_param(check_out_raw)

    try:
        adults = max(1, int(adults_raw))
    except (ValueError, TypeError):
        adults = 2

    try:
        children = max(0, int(children_raw))
    except (ValueError, TypeError):
        children = 0

    dates_valid = False
    is_available = True
    nights = 1
    total_price = room.price_per_night

    if check_in and check_out:
        today = timezone.localdate()
        if check_in >= today and check_out > check_in:
            dates_valid = True
            is_booked = Booking.objects.filter(
                get_overlapping_bookings_query(check_in, check_out),
                room=room
            ).exists()
            is_available = not is_booked
            nights, total_price = calculate_total_price(room.price_per_night, check_in, check_out)

    context = {
        'room': room,
        'hotel': room.hotel,
        'check_in': check_in.isoformat() if check_in else '',
        'check_out': check_out.isoformat() if check_out else '',
        'adults': adults,
        'children': children,
        'dates_valid': dates_valid,
        'is_available': is_available,
        'nights': nights,
        'total_price': total_price,
    }
    return render(request, 'hotels/room_detail.html', context)
