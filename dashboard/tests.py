from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from accounts.models import UserRole
from hotels.models import Hotel, Room, RoomType
from bookings.models import Booking, BookingStatus
from reviews.models import Review

User = get_user_model()


class DashboardAndReviewSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Manager 1
        self.manager1 = User.objects.create_user(
            username='mgr_alpha',
            email='m1@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        # Manager 2
        self.manager2 = User.objects.create_user(
            username='mgr_beta',
            email='m2@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        # Customer
        self.customer = User.objects.create_user(
            username='cust_regular',
            email='c@staybook.uz',
            password='Password123!',
            role=UserRole.CUSTOMER
        )

        # Hotel 1 (Manager 1)
        self.hotel1 = Hotel.objects.create(
            manager=self.manager1,
            name='Hotel Alpha Tashkent',
            city='Toshkent',
            address='Bobur 1',
            stars=4
        )
        self.room1 = Room.objects.create(
            hotel=self.hotel1,
            number='101',
            title='Deluxe Room',
            price_per_night=Decimal('500000')
        )

        # Hotel 2 (Manager 2)
        self.hotel2 = Hotel.objects.create(
            manager=self.manager2,
            name='Hotel Beta Samarkand',
            city='Samarqand',
            address='Registon 2',
            stars=5
        )
        self.room2 = Room.objects.create(
            hotel=self.hotel2,
            number='201',
            title='Suite Room',
            price_per_night=Decimal('800000')
        )

    def test_customer_cannot_access_dashboard(self):
        """Regular customer must be denied access to manager dashboard."""
        self.client.login(username='cust_regular', password='Password123!')
        url = reverse('dashboard:overview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_manager_sees_only_own_hotels_in_dashboard(self):
        """Manager 1 should only see Hotel 1, never Hotel 2."""
        self.client.login(username='mgr_alpha', password='Password123!')
        url = reverse('dashboard:hotels')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hotel Alpha Tashkent')
        self.assertNotContains(response, 'Hotel Beta Samarkand')

    def test_manager_cannot_modify_other_managers_room(self):
        """Manager 1 cannot toggle or edit Manager 2's room."""
        self.client.login(username='mgr_alpha', password='Password123!')
        url = reverse('dashboard:rooms')
        # Attempt to toggle Manager 2's room
        response = self.client.post(url, {
            'action': 'toggle_active',
            'room_id': self.room2.id
        })
        self.assertEqual(response.status_code, 404)

    def test_review_allowed_only_for_completed_booking_by_owner(self):
        """Review can only be created by the booking owner when status is COMPLETED."""
        today = timezone.localdate()
        booking = Booking.objects.create(
            user=self.customer,
            room=self.room1,
            check_in=today - timedelta(days=5),
            check_out=today - timedelta(days=2),
            adults=2,
            children=0,
            guest_name='Regular Customer',
            guest_phone='+998901234567',
            nightly_price_snapshot=Decimal('500000'),
            total_price=Decimal('1500000'),
            status=BookingStatus.PENDING  # Not completed yet
        )

        review_url = reverse('reviews:create', kwargs={'booking_id': booking.id})

        # 1. PENDING booking review attempt -> should be rejected
        self.client.login(username='cust_regular', password='Password123!')
        response_pending = self.client.post(review_url, {
            'rating': '5',
            'comment': 'Ajoyib mehmonxona!'
        })
        self.assertFalse(Review.objects.filter(booking=booking).exists())

        # 2. Update to COMPLETED
        booking.status = BookingStatus.COMPLETED
        booking.save()

        # 3. Another user cannot review customer's booking
        self.client.login(username='mgr_alpha', password='Password123!')
        response_unauthorized = self.client.post(review_url, {
            'rating': '5',
            'comment': 'Sharh'
        })
        self.assertEqual(response_unauthorized.status_code, 403)

        # 4. Owner creates review for COMPLETED booking -> succeeds
        self.client.login(username='cust_regular', password='Password123!')
        response_success = self.client.post(review_url, {
            'rating': '5',
            'comment': 'Haqiqatan ham juda ajoyib mehmonxona, toza va shinam!'
        })
        self.assertEqual(response_success.status_code, 302)
        self.assertTrue(Review.objects.filter(booking=booking).exists())
        review = Review.objects.get(booking=booking)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.hotel, self.hotel1)

        # 5. Cannot create duplicate review for same booking
        response_duplicate = self.client.post(review_url, {
            'rating': '4',
            'comment': 'Ikkinchi sharh'
        })
        self.assertEqual(Review.objects.filter(booking=booking).count(), 1)
