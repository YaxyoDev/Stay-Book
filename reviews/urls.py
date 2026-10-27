from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('create/<uuid:booking_id>/', views.review_create_view, name='create'),
]
