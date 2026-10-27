from datetime import date, timedelta
from decimal import Decimal
import threading
from django.test import TestCase, TransactionTestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import connection

from accounts.models import UserRole
from hotels.models import Hotel, Room, RoomType
from bookings.models import Booking, BookingStatus
from bookings.services import create_booking_atomic, is_room_available, cancel_booking

User = get_user_model()


class BookingLogicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username='mgr1',
            email='mgr1@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        self.other_manager = User.objects.create_user(
            username='mgr2',
            email='mgr2@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        self.customer = User.objects.create_user(
            username='cust1',
            email='cust1@staybook.uz',
            password='Password123!',
            role=UserRole.CUSTOMER
        )
        self.other_customer = User.objects.create_user(
            username='cust2',
            email='cust2@staybook.uz',
            password='Password123!',
            role=UserRole.CUSTOMER
        )

        self.hotel = Hotel.objects.create(
            manager=self.manager,
            name='Silk Road Grand Hotel',
            city='Toshkent',
            address='Bobur ko‘chasi 45',
            stars=5,
            is_published=True
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            number='101',
            title='Deluxe King Room',
            room_type=RoomType.DELUXE,
            capacity_adults=2,
            capacity_children=1,
            price_per_night=Decimal('600000'),
            is_active=True
        )

    def test_past_dates_rejected(self):
        today = timezone.localdate()
        past_check_in = today - timedelta(days=5)
        past_check_out = today - timedelta(days=2)

        with self.assertRaises(ValidationError):
            create_booking_atomic(
                user=self.customer,
                room_id=self.room.id,
                check_in=past_check_in,
                check_out=past_check_out,
                adults=2,
                children=0,
                guest_name='Alisher Usmonov',
                guest_phone='+998901234567'
            )

    def test_checkout_before_or_equal_checkin_rejected(self):
        today = timezone.localdate() + timedelta(days=5)
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                user=self.customer,
                room_id=self.room.id,
                check_in=today,
                check_out=today,  # 0 nights
                adults=2,
                children=0,
                guest_name='Alisher Usmonov',
                guest_phone='+998901234567'
            )

    def test_capacity_exceeded_rejected(self):
        today = timezone.localdate() + timedelta(days=5)
        # Room allows max 2 adults, total 3 guests
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                user=self.customer,
                room_id=self.room.id,
                check_in=today,
                check_out=today + timedelta(days=2),
                adults=3,  # Exceeds capacity_adults=2
                children=0,
                guest_name='Alisher Usmonov',
                guest_phone='+998901234567'
            )

    def test_date_overlap_formula(self):
        """
        Tests specification formula:
        existing.check_in < new_check_out AND existing.check_out > new_check_in
        Book 10-13 Nov (base).
        11-12 Nov: Reject
        12-14 Nov: Reject
        9-11 Nov: Reject
        13-15 Nov: ALLOWED (13 is checkout day)
        7-10 Nov: ALLOWED (10 is checkin day)
        """
        today = timezone.localdate() + timedelta(days=10)
        base_in = today
        base_out = today + timedelta(days=3)  # 3 nights

        # 1. Create base booking (e.g. 10-13)
        booking1 = create_booking_atomic(
            user=self.customer,
            room_id=self.room.id,
            check_in=base_in,
            check_out=base_out,
            adults=2,
            children=0,
            guest_name='Alisher Usmonov',
            guest_phone='+998901234567'
        )
        self.assertIsNotNone(booking1)

        # 2. Inside overlap: 11-12 -> Should fail
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                user=self.other_customer,
                room_id=self.room.id,
                check_in=base_in + timedelta(days=1),
                check_out=base_in + timedelta(days=2),
                adults=1,
                children=0,
                guest_name='Sardor',
                guest_phone='+998909998877'
            )

        # 3. Overlap on right: 12-14 -> Should fail
        with self.assertRaises(ValidationError):
            create_booking_atomic(
                user=self.other_customer,
                room_id=self.room.id,
                check_in=base_in + timedelta(days=2),
                check_out=base_out + timedelta(days=1),
                adults=1,
                children=0,
                guest_name='Sardor',
                guest_phone='+998909998877'
            )

        # 4. Adjacent check-out day: 13-15 -> MUST SUCCEED
        booking_adjacent_after = create_booking_atomic(
            user=self.other_customer,
            room_id=self.room.id,
            check_in=base_out,
            check_out=base_out + timedelta(days=2),
            adults=1,
            children=0,
            guest_name='Sardor',
            guest_phone='+998909998877'
        )
        self.assertIsNotNone(booking_adjacent_after)

        # 5. Adjacent check-in day: 7-10 -> MUST SUCCEED
        booking_adjacent_before = create_booking_atomic(
            user=self.other_customer,
            room_id=self.room.id,
            check_in=base_in - timedelta(days=3),
            check_out=base_in,
            adults=1,
            children=0,
            guest_name='Botir',
            guest_phone='+998901112233'
        )
        self.assertIsNotNone(booking_adjacent_before)

    def test_cancelled_booking_frees_up_room(self):
        today = timezone.localdate() + timedelta(days=20)
        c_in = today
        c_out = today + timedelta(days=3)

        booking = create_booking_atomic(
            user=self.customer,
            room_id=self.room.id,
            check_in=c_in,
            check_out=c_out,
            adults=2,
            children=0,
            guest_name='Alisher',
            guest_phone='+998901234567'
        )

        # Cancel the booking
        cancel_booking(booking, actor=self.customer)
        self.assertEqual(booking.status, BookingStatus.CANCELLED)

        # New booking for exact same dates should now succeed!
        new_booking = create_booking_atomic(
            user=self.other_customer,
            room_id=self.room.id,
            check_in=c_in,
            check_out=c_out,
            adults=2,
            children=0,
            guest_name='Jasur',
            guest_phone='+998905556677'
        )
        self.assertIsNotNone(new_booking)

    def test_server_side_price_calculation_untrusted_client(self):
        """Price snapshot and total are calculated on server side."""
        today = timezone.localdate() + timedelta(days=30)
        c_in = today
        c_out = today + timedelta(days=4)  # 4 nights

        booking = create_booking_atomic(
            user=self.customer,
            room_id=self.room.id,
            check_in=c_in,
            check_out=c_out,
            adults=2,
            children=0,
            guest_name='Alisher',
            guest_phone='+998901234567'
        )

        expected_total = Decimal('600000') * 4  # 2,400,000
        self.assertEqual(booking.nightly_price_snapshot, Decimal('600000'))
        self.assertEqual(booking.total_price, expected_total)

        # If room price changes later, historical booking total does NOT change
        self.room.price_per_night = Decimal('990000')
        self.room.save()

        booking.refresh_from_db()
        self.assertEqual(booking.total_price, expected_total)

    def test_booking_detail_permissions(self):
        today = timezone.localdate() + timedelta(days=40)
        booking = create_booking_atomic(
            user=self.customer,
            room_id=self.room.id,
            check_in=today,
            check_out=today + timedelta(days=2),
            adults=2,
            children=0,
            guest_name='Alisher',
            guest_phone='+998901234567'
        )

        url = reverse('bookings:detail', kwargs={'pk': booking.pk})

        # 1. Owner can view
        self.client.login(username='cust1', password='Password123!')
        res_owner = self.client.get(url)
        self.assertEqual(res_owner.status_code, 200)

        # 2. Hotel Manager can view
        self.client.login(username='mgr1', password='Password123!')
        res_mgr = self.client.get(url)
        self.assertEqual(res_mgr.status_code, 200)

        # 3. Other customer gets 403 Forbidden
        self.client.login(username='cust2', password='Password123!')
        res_other = self.client.get(url)
        self.assertEqual(res_other.status_code, 403)

        # 4. Other manager gets 403 Forbidden
        self.client.login(username='mgr2', password='Password123!')
        res_other_mgr = self.client.get(url)
        self.assertEqual(res_other_mgr.status_code, 403)

    def test_cancel_permission(self):
        today = timezone.localdate() + timedelta(days=50)
        booking = create_booking_atomic(
            user=self.customer,
            room_id=self.room.id,
            check_in=today,
            check_out=today + timedelta(days=2),
            adults=2,
            children=0,
            guest_name='Alisher',
            guest_phone='+998901234567'
        )

        cancel_url = reverse('bookings:cancel', kwargs={'pk': booking.pk})

        # Other customer cannot cancel
        self.client.login(username='cust2', password='Password123!')
        res_other = self.client.post(cancel_url)
        self.assertEqual(res_other.status_code, 403)

        # Owner can cancel
        self.client.login(username='cust1', password='Password123!')
        res_owner = self.client.post(cancel_url)
        self.assertEqual(res_owner.status_code, 302)
        booking.refresh_from_db()
        self.assertEqual(booking.status, BookingStatus.CANCELLED)


class BookingConcurrencyTests(TransactionTestCase):
    """
    Test parallel booking creation attempts using TransactionTestCase
    to verify select_for_update() row lock and race condition prevention.
    """
    def setUp(self):
        self.manager = User.objects.create_user(
            username='c_mgr',
            email='c_mgr@staybook.uz',
            password='Password123!',
            role=UserRole.MANAGER
        )
        self.user1 = User.objects.create_user(
            username='user_a',
            email='user_a@staybook.uz',
            password='Password123!',
            role=UserRole.CUSTOMER
        )
        self.user2 = User.objects.create_user(
            username='user_b',
            email='user_b@staybook.uz',
            password='Password123!',
            role=UserRole.CUSTOMER
        )
        self.hotel = Hotel.objects.create(
            manager=self.manager,
            name='Concurrency Grand Hotel',
            city='Toshkent',
            address='Amir Temur 1',
            stars=5,
            is_published=True
        )
        self.room = Room.objects.create(
            hotel=self.hotel,
            number='505',
            title='Royal Suite',
            room_type=RoomType.SUITE,
            capacity_adults=2,
            price_per_night=Decimal('1000000'),
            is_active=True
        )

    def test_parallel_concurrent_bookings_only_one_succeeds(self):
        today = timezone.localdate() + timedelta(days=60)
        check_in = today
        check_out = today + timedelta(days=3)

        results = []
        errors = []

        def book_attempt(user, guest_name):
            try:
                # Close any old connection in thread so a clean connection is established
                connection.close()
                b = create_booking_atomic(
                    user=user,
                    room_id=self.room.id,
                    check_in=check_in,
                    check_out=check_out,
                    adults=2,
                    children=0,
                    guest_name=guest_name,
                    guest_phone='+998901234567'
                )
                results.append(b)
            except ValidationError as e:
                errors.append(str(e))
            finally:
                connection.close()

        t1 = threading.Thread(target=book_attempt, args=(self.user1, 'User One'))
        t2 = threading.Thread(target=book_attempt, args=(self.user2, 'User Two'))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Exactly ONE booking must succeed, and the other must fail due to room lock / overlap!
        self.assertEqual(len(results), 1, f"Expected exactly 1 booking to succeed, got {len(results)}")
        self.assertEqual(len(errors), 1, f"Expected 1 booking to fail with ValidationError, got {len(errors)}")
        self.assertEqual(Booking.objects.filter(room=self.room).count(), 1)
