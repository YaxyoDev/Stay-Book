from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role', 'phone', 'avatar')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Qo‘shimcha ma’lumotlar', {'fields': ('role', 'email', 'phone', 'avatar')}),
    )
