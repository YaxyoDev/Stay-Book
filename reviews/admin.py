from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'user', 'rating', 'created_at', 'is_visible')
    list_filter = ('rating', 'is_visible', 'hotel')
    search_fields = ('hotel__name', 'user__username', 'comment')
