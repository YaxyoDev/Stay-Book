from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_overview, name='overview'),
    path('hotels/', views.dashboard_hotels, name='hotels'),
    path('rooms/', views.dashboard_rooms, name='rooms'),
    path('bookings/', views.dashboard_bookings, name='bookings'),
]
