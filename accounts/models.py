from django.contrib.auth.models import AbstractUser
from django.db import models


class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Mijoz'
    MANAGER = 'MANAGER', 'Mehmonxona menejeri'


class User(AbstractUser):
    email = models.EmailField('Email manzili', unique=True)
    phone = models.CharField('Telefon raqami', max_length=20, blank=True)
    role = models.CharField(
        'Foydalanuvchi roli',
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        help_text='Mijoz yoki mehmonxona menejeri roli'
    )
    avatar = models.ImageField('Profil rasmi', upload_to='avatars/', blank=True, null=True)

    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-date_joined']

    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.username

    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER or self.is_superuser

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER
