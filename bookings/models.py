import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class BookingStatus(models.TextChoices):
    PENDING = 'PENDING', 'Kutilmoqda'
    CONFIRMED = 'CONFIRMED', 'Tasdiqlangan'
    CANCELLED = 'CANCELLED', 'Bekor qilingan'
    REJECTED = 'REJECTED', 'Rad etilgan'
    COMPLETED = 'COMPLETED', 'Yakunlangan'


class Booking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Foydalanuvchi'
    )
    room = models.ForeignKey(
        'hotels.Room',
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Xona'
    )
    check_in = models.DateField('Kirish sanasi', db_index=True)
    check_out = models.DateField('Chiqish sanasi', db_index=True)
    adults = models.PositiveSmallIntegerField('Kattalar soni', default=1)
    children = models.PositiveSmallIntegerField('Bolalar soni', default=0)
    guest_name = models.CharField('Mehmon to‘liq ismi', max_length=150)
    guest_phone = models.CharField('Mehmon telefoni', max_length=30)
    nightly_price_snapshot = models.DecimalField(
        'Tungi narx snapshot (so‘m)',
        max_digits=12,
        decimal_places=2
    )
    total_price = models.DecimalField(
        'Jami hisoblangan narx (so‘m)',
        max_digits=12,
        decimal_places=2
    )
    status = models.CharField(
        'Bron holati',
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.PENDING,
        db_index=True
    )
    special_requests = models.TextField('Maxsus istaklar', blank=True)
    created_at = models.DateTimeField('Yaratilgan vaqt', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan vaqt', auto_now=True)
    cancelled_at = models.DateTimeField('Bekor qilingan vaqt', null=True, blank=True)

    class Meta:
        verbose_name = 'Bron'
        verbose_name_plural = 'Bronlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"Bron #{str(self.id)[:8]} - {self.room.hotel.name} ({self.guest_name})"

    @property
    def nights(self):
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    @property
    def total_guests(self):
        return self.adults + self.children

    @property
    def is_blocking(self):
        """Returns True if this booking occupies the room."""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]

    @property
    def can_cancel(self):
        """Customer can cancel if booking is pending or confirmed and check_in is in the future."""
        today = timezone.localdate()
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED] and self.check_in >= today

    def clean(self):
        if self.check_in and self.check_out:
            if self.check_in >= self.check_out:
                raise ValidationError("Chiqish sanasi kirish sanasidan keyin bo‘lishi shart.")
            if self.nights < 1:
                raise ValidationError("Minimal bron muddati 1 kecha.")
            if self.nights > 30:
                raise ValidationError("Maksimal bron muddati 30 kecha.")


class BookingStatusLog(models.Model):
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name='Bron'
    )
    old_status = models.CharField('Eski holat', max_length=20, choices=BookingStatus.choices)
    new_status = models.CharField('Yangi holat', max_length=20, choices=BookingStatus.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Amalni bajargan shaxs'
    )
    note = models.TextField('Izoh', blank=True)
    created_at = models.DateTimeField('O‘zgarish vaqti', auto_now_add=True)

    class Meta:
        verbose_name = 'Bron holati tarixi'
        verbose_name_plural = 'Bron holatlari tarixi'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking.id}: {self.old_status} -> {self.new_status}"
