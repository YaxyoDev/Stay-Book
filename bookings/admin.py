from django.contrib import admin
from .models import Booking, BookingStatusLog


class BookingStatusLogInline(admin.TabularInline):
    model = BookingStatusLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'actor', 'note', 'created_at')
    can_delete = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'guest_name', 'guest_phone', 'check_in', 'check_out', 'total_price', 'status', 'created_at')
    list_filter = ('status', 'check_in', 'check_out', 'room__hotel')
    search_fields = ('id', 'guest_name', 'guest_phone', 'user__username', 'room__number', 'room__hotel__name')
    readonly_fields = ('id', 'nightly_price_snapshot', 'total_price', 'created_at', 'updated_at', 'cancelled_at')
    inlines = [BookingStatusLogInline]


@admin.register(BookingStatusLog)
class BookingStatusLogAdmin(admin.ModelAdmin):
    list_display = ('booking', 'old_status', 'new_status', 'actor', 'created_at')
    list_filter = ('new_status', 'created_at')
    readonly_fields = ('booking', 'old_status', 'new_status', 'actor', 'note', 'created_at')
