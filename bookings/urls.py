from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.booking_list_view, name='list'),
    path('create/<int:room_id>/', views.booking_create_view, name='create'),
    path('<uuid:pk>/', views.booking_detail_view, name='detail'),
    path('<uuid:pk>/cancel/', views.booking_cancel_view, name='cancel'),
]
