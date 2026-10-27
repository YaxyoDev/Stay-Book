"""
StayBook URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hotels.views import hotel_list_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', hotel_list_view, name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('hotels/', include('hotels.urls', namespace='hotels')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
