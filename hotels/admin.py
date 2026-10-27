from django.contrib import admin
from .models import Amenity, Hotel, HotelImage, Room, RoomImage


class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 1
    fields = ('image', 'alt_text', 'sort_order', 'is_primary')


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1
    fields = ('image', 'sort_order', 'is_primary')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'stars', 'manager', 'contact_phone', 'is_published', 'created_at')
    list_filter = ('city', 'stars', 'is_published')
    search_fields = ('name', 'city', 'address', 'manager__username', 'manager__email')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('amenities',)
    inlines = [HotelImageInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'number', 'title', 'room_type', 'capacity_adults', 'capacity_children', 'price_per_night', 'is_active')
    list_filter = ('hotel', 'room_type', 'is_active')
    search_fields = ('number', 'title', 'hotel__name')
    inlines = [RoomImageInline]


@admin.register(HotelImage)
class HotelImageAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'alt_text', 'sort_order', 'is_primary')
    list_filter = ('hotel', 'is_primary')


@admin.register(RoomImage)
class RoomImageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sort_order', 'is_primary')
    list_filter = ('room__hotel', 'is_primary')
