from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Review(models.Model):
    hotel = models.ForeignKey(
        'hotels.Hotel',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Mehmonxona'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Foydalanuvchi'
    )
    booking = models.OneToOneField(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Tegishli bron'
    )
    rating = models.PositiveSmallIntegerField(
        'Baholash (1 dan 5 gacha)',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField('Foydalanuvchi sharhi')
    created_at = models.DateTimeField('Qoldirilgan vaqt', auto_now_add=True)
    is_visible = models.BooleanField('Saytda ko‘rsatilsinmi', default=True, db_index=True)

    class Meta:
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.hotel.name} ({self.rating}★)"

    def clean(self):
        if hasattr(self, 'booking') and self.booking:
            if self.booking.status != 'COMPLETED':
                raise ValidationError("Faqat yakunlangan (COMPLETED) bronlar uchun sharh qoldirish mumkin.")
            if self.booking.user != self.user:
                raise ValidationError("Ushbu bron sizga tegishli emas.")
            if self.booking.room.hotel != self.hotel:
                raise ValidationError("Bron qilingan mehmonxona bilan sharh mehmonxonasi mos kelmadi.")
