from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class Amenity(models.Model):
    name = models.CharField('Qulaylik nomi', max_length=100, unique=True)
    icon = models.CharField(
        'Material Symbol ikonkasi',
        max_length=50,
        blank=True,
        help_text='masalan: wifi, pool, restaurant, fitness_center, local_parking, ac_unit'
    )

    class Meta:
        verbose_name = 'Qulaylik'
        verbose_name_plural = 'Qulayliklar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Hotel(models.Model):
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hotels',
        verbose_name='Mehmonxona menejeri'
    )
    name = models.CharField('Mehmonxona nomi', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True, blank=True)
    description = models.TextField('Batafsil tavsif')
    city = models.CharField('Shahar', max_length=100, db_index=True)
    address = models.CharField('To‘liq manzil', max_length=300)
    latitude = models.DecimalField('Kenglik (Latitude)', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Uzunlik (Longitude)', max_digits=9, decimal_places=6, null=True, blank=True)
    stars = models.PositiveSmallIntegerField(
        'Yulduzlar soni',
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    contact_phone = models.CharField('Aloqa telefoni', max_length=30, blank=True)
    contact_email = models.EmailField('Aloqa emaili', blank=True)
    check_in_time = models.TimeField('Kirish vaqti (Check-in)', default='14:00')
    check_out_time = models.TimeField('Chiqish vaqti (Check-out)', default='12:00')
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='hotels', verbose_name='Qulayliklar')
    is_published = models.BooleanField('Saytda ko‘rsatilsinmi', default=True, db_index=True)
    created_at = models.DateTimeField('Yaratilgan sana', auto_now_add=True)
    updated_at = models.DateTimeField('O‘zgartirilgan sana', auto_now=True)

    class Meta:
        verbose_name = 'Mehmonxona'
        verbose_name_plural = 'Mehmonxonalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.city})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Hotel.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('hotels:detail', kwargs={'slug': self.slug})

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.order_by('sort_order', 'id').first()
        return img

    @property
    def average_rating(self):
        # We will aggregate from reviews if reviews app is queried
        reviews = self.reviews.filter(is_visible=True)
        if reviews.exists():
            val = reviews.aggregate(models.Avg('rating'))['rating__avg']
            return round(val, 1) if val else None
        return None

    @property
    def review_count(self):
        return self.reviews.filter(is_visible=True).count()

    @property
    def min_price(self):
        active_rooms = self.rooms.filter(is_active=True)
        if active_rooms.exists():
            return active_rooms.aggregate(models.Min('price_per_night'))['price_per_night__min']
        return None


class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images', verbose_name='Mehmonxona')
    image = models.ImageField('Surat', upload_to='hotels/')
    alt_text = models.CharField('Rasm tavsifi', max_length=255, blank=True)
    sort_order = models.PositiveIntegerField('Tartib raqami', default=0)
    is_primary = models.BooleanField('Asosiy surat', default=False)

    class Meta:
        verbose_name = 'Mehmonxona surati'
        verbose_name_plural = 'Mehmonxona suratlari'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.hotel.name} - Surat #{self.id}"


class RoomType(models.TextChoices):
    STANDARD = 'STANDARD', 'Standard'
    DELUXE = 'DELUXE', 'Deluxe'
    SUITE = 'SUITE', 'Suite'


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms', verbose_name='Mehmonxona')
    number = models.CharField('Xona raqami', max_length=20)
    title = models.CharField('Xona nomi / toifasi', max_length=150)
    description = models.TextField('Xona haqida', blank=True)
    room_type = models.CharField(
        'Xona toifasi',
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.STANDARD
    )
    capacity_adults = models.PositiveSmallIntegerField(
        'Kattalar sig‘imi',
        default=2,
        validators=[MinValueValidator(1)]
    )
    capacity_children = models.PositiveSmallIntegerField('Bolalar sig‘imi', default=0)
    price_per_night = models.DecimalField(
        'Bir kecha narxi (so‘m)',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField('Xona faolmi', default=True, db_index=True)
    created_at = models.DateTimeField('Qo‘shilgan sana', auto_now_add=True)
    updated_at = models.DateTimeField('O‘zgartirilgan sana', auto_now=True)

    class Meta:
        verbose_name = 'Xona'
        verbose_name_plural = 'Xonalar'
        constraints = [
            models.UniqueConstraint(fields=['hotel', 'number'], name='unique_hotel_room_number')
        ]
        ordering = ['hotel', 'number']

    def __str__(self):
        return f"{self.hotel.name} - {self.number} ({self.title})"

    @property
    def total_capacity(self):
        return self.capacity_adults + self.capacity_children

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.order_by('sort_order', 'id').first()
        return img


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images', verbose_name='Xona')
    image = models.ImageField('Surat', upload_to='rooms/')
    sort_order = models.PositiveIntegerField('Tartib raqami', default=0)
    is_primary = models.BooleanField('Asosiy surat', default=False)

    class Meta:
        verbose_name = 'Xona surati'
        verbose_name_plural = 'Xona suratlari'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.room} - Surat #{self.id}"
