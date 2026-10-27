from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from accounts.models import UserRole
from hotels.models import Hotel, Room, Amenity, RoomType

User = get_user_model()


class HotelAndRoomTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username='hotelmanager',
            email='hm@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        self.hotel = Hotel.objects.create(
            manager=self.manager,
            name='Grand Bukhara Hotel',
            city='Buxoro',
            address='Eski shahar, 12-uy',
            stars=4,
            description='Ajoyib qulay mehmonxona',
            is_published=True
        )
        self.amenity = Amenity.objects.create(name='Wi-Fi', icon='wifi')
        self.hotel.amenities.add(self.amenity)

        self.room1 = Room.objects.create(
            hotel=self.hotel,
            number='101',
            title='Deluxe Double Room',
            room_type=RoomType.DELUXE,
            capacity_adults=2,
            capacity_children=1,
            price_per_night=Decimal('500000'),
            is_active=True
        )

    def test_hotel_slug_auto_generation(self):
        self.assertEqual(self.hotel.slug, 'grand-bukhara-hotel')

    def test_room_unique_number_in_same_hotel(self):
        # Same room number in same hotel should raise IntegrityError
        with self.assertRaises(IntegrityError):
            Room.objects.create(
                hotel=self.hotel,
                number='101',
                title='Another Room',
                price_per_night=Decimal('600000')
            )

    def test_room_same_number_in_different_hotel(self):
        # Same room number in different hotel is allowed
        another_hotel = Hotel.objects.create(
            manager=self.manager,
            name='Tashkent Grand Palace',
            city='Toshkent',
            address='Amir Temur ko\'chasi',
            stars=5
        )
        room_other = Room.objects.create(
            hotel=another_hotel,
            number='101',
            title='Standard Room',
            price_per_night=Decimal('400000')
        )
        self.assertEqual(room_other.number, '101')

    def test_hotel_list_view_public_access(self):
        url = reverse('hotels:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grand Bukhara Hotel')

    def test_hotel_list_search_by_city(self):
        url = reverse('hotels:list')
        response = self.client.get(url, {'city': 'Buxoro'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grand Bukhara Hotel')

        response_empty = self.client.get(url, {'city': 'Andijon'})
        self.assertEqual(response_empty.status_code, 200)
        self.assertNotContains(response_empty, 'Grand Bukhara Hotel')

    def test_hotel_detail_view(self):
        url = reverse('hotels:detail', kwargs={'slug': self.hotel.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grand Bukhara Hotel')
        self.assertContains(response, 'Deluxe Double Room')

    def test_room_detail_view(self):
        url = reverse('hotels:room_detail', kwargs={'pk': self.room1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Deluxe Double Room')
        self.assertContains(response, '500000')
