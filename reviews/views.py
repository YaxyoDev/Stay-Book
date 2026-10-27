from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib import messages

from bookings.models import Booking, BookingStatus
from .models import Review


@login_required
@require_POST
def review_create_view(request, booking_id):
    booking = get_object_or_404(Booking.objects.select_related('room__hotel'), pk=booking_id)

    # Permission checks
    if booking.user != request.user:
        raise PermissionDenied("Siz faqat o‘zingizning broningiz uchun sharh qoldirishingiz mumkin.")

    if booking.status != BookingStatus.COMPLETED:
        messages.error(request, "Faqat yakunlangan (COMPLETED) sayohatlar uchun sharh qoldirish mumkin.")
        return redirect('bookings:detail', pk=booking.pk)

    if hasattr(booking, 'review'):
        messages.warning(request, "Ushbu bron uchun allaqachon sharh qoldirilgan.")
        return redirect('bookings:detail', pk=booking.pk)

    rating_raw = request.POST.get('rating', '5')
    comment = request.POST.get('comment', '').strip()

    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            raise ValueError()
    except ValueError:
        rating = 5

    if not comment:
        messages.error(request, "Iltimos, sharh matnini kiriting.")
        return redirect('bookings:detail', pk=booking.pk)

    review = Review.objects.create(
        hotel=booking.room.hotel,
        user=request.user,
        booking=booking,
        rating=rating,
        comment=comment,
        is_visible=True
    )

    messages.success(request, "Sharhingiz muvaffaqiyatli qabul qilindi. Fikringiz uchun tashakkur!")
    return redirect('bookings:detail', pk=booking.pk)
