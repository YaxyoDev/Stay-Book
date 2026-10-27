"""
StayBook URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from hotels.views import home_view, room_detail_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('rooms/<int:pk>/', room_detail_view, name='direct_room_detail'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('hotels/', include('hotels.urls', namespace='hotels')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
