from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import UserRole
from hotels.models import Amenity, Hotel, Room, RoomType
from bookings.models import Booking, BookingStatus, BookingStatusLog
from reviews.models import Review

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with realistic hotels, rooms, amenities, managers, and sample bookings"

    def handle(self, *args, **options):
        self.stdout.write("Seeding StayBook database...")

        # 1. Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@staybook.uz',
                'first_name': 'Admin',
                'last_name': 'StayBook',
                'role': UserRole.MANAGER,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin1234')
            admin_user.save()
            self.stdout.write("Created superuser: admin / admin1234")

        # 2. Manager
        manager_user, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager@staybook.uz',
                'first_name': 'Jamshid',
                'last_name': 'Karimov',
                'role': UserRole.MANAGER,
                'phone': '+998901234567',
                'is_staff': False,
            }
        )
        if created:
            manager_user.set_password('manager1234')
            manager_user.save()
            self.stdout.write("Created manager: manager1 / manager1234")

        # 3. Customer
        customer_user, created = User.objects.get_or_create(
            username='customer1',
            defaults={
                'email': 'customer@staybook.uz',
                'first_name': 'Alisher',
                'last_name': 'Usmonov',
                'role': UserRole.CUSTOMER,
                'phone': '+998909876543',
            }
        )
        if created:
            customer_user.set_password('customer1234')
            customer_user.save()
            self.stdout.write("Created customer: customer1 / customer1234")

        # 4. Amenities
        amenities_data = [
            ('Bepul yuqori tezlikdagi Wi-Fi', 'wifi'),
            ('Basseyn va dam olish zonasi', 'pool'),
            ('Nonushta kiritilgan', 'restaurant'),
            ('Konditsioner tizimi', 'ac_unit'),
            ('Avtoturargoh', 'local_parking'),
            ('Fitnes zali', 'fitness_center'),
            ('Spa & Sauna', 'spa'),
            ('24/7 qabulxona', 'concierge'),
            ('Aeroport transferi', 'airport_shuttle'),
        ]
        amenities_objs = []
        for name, icon in amenities_data:
            amenity, _ = Amenity.objects.get_or_create(name=name, defaults={'icon': icon})
            amenities_objs.append(amenity)

        # 5. Hotels
        hotels_data = [
            {
                'name': 'Silk Road Grand Hotel',
                'city': 'Toshkent',
                'address': 'Toshkent shahri, Yakkasaroy tumani, Bobur ko\'chasi 45-uy',
                'stars': 5,
                'contact_phone': '+998 71 200 45 45',
                'description': 'Silk Road Grand Hotel — Toshkent markazida joylashgan zamonaviy 5 yulduzli lyuks mehmonxona. Mehmonlar uchun qulay xonalar, xalqaro restoran, yopiq suzish havzasi va eng yuqori darajadagi servis xizmati taqdim etiladi.',
            },
            {
                'name': 'Registan Heritage Palace',
                'city': 'Samarqand',
                'address': 'Samarqand shahri, Registon ko\'chasi 12-uy',
                'stars': 5,
                'contact_phone': '+998 66 233 11 22',
                'description': 'Registon maydoniga bir necha daqiqalik piyoda masofada joylashgan an\'anaviy sharqona uslubdagi hashamatli mehmonxona. O\'zbek milliy me\'morchiligi va zamonaviy qulayliklarning ajoyib uyg\'unligi.',
            },
            {
                'name': 'Minzifa Boutique Hotel',
                'city': 'Buxoro',
                'address': 'Buxoro shahri, Xo\'ja Ruxshon ko\'chasi 6-uy',
                'stars': 4,
                'contact_phone': '+998 65 224 55 77',
                'description': 'Labi Hovuz ansambli yaqinidagi shinam butik mehmonxona. Qadimiy naqshlar bilan bezatilgan xonalar, sokin hovli va Buxoroning haqiqiy mehmondo\'stlik muhiti.',
            },
            {
                'name': 'Orient Star Khiva Hotel',
                'city': 'Xiva',
                'address': 'Xiva shahri, Ichan Qal\'a, Pahlavon Mahmud ko\'chasi 1-uy',
                'stars': 4,
                'contact_phone': '+998 62 375 88 99',
                'description': 'Tarixiy Muhammad Aminxon madrasasi binosida joylashgan betakror mehmonxona. Qadimiy devorlar va minoralar bag\'rida unutilmas tunlarni o\'tkazing.',
            },
            {
                'name': 'Zomin Mountain Resort & Spa',
                'city': 'Zomin',
                'address': 'Jizzax viloyati, Zomin tumani, O\'rmon xo\'jaligi hududi',
                'stars': 4,
                'contact_phone': '+998 72 221 00 11',
                'description': 'Zomin milliy bog\'i bag\'rida, toza tog\' havosi va archazorlar qurshovida joylashgan ekologik kurort mehmonxonasi. Oilaviy dam olish va salomatlikni tiklash maskani.',
            },
        ]

        for hdata in hotels_data:
            hotel, hcreated = Hotel.objects.get_or_create(
                name=hdata['name'],
                defaults={
                    'manager': manager_user,
                    'city': hdata['city'],
                    'address': hdata['address'],
                    'stars': hdata['stars'],
                    'contact_phone': hdata['contact_phone'],
                    'description': hdata['description'],
                    'is_published': True,
                }
            )
            hotel.amenities.set(amenities_objs[:6])

            # Create Rooms for each hotel
            rooms_specs = [
                ('101', 'Standard Single Room', RoomType.STANDARD, 1, 0, Decimal('350000')),
                ('102', 'Standard Double Room', RoomType.STANDARD, 2, 0, Decimal('450000')),
                ('201', 'Deluxe King Room', RoomType.DELUXE, 2, 1, Decimal('650000')),
                ('202', 'Deluxe Twin Room', RoomType.DELUXE, 2, 1, Decimal('650000')),
                ('301', 'Executive Panoramic Suite', RoomType.SUITE, 3, 2, Decimal('1100000')),
            ]

            for num, title, rtype, cadults, ckids, price in rooms_specs:
                room, _ = Room.objects.get_or_create(
                    hotel=hotel,
                    number=num,
                    defaults={
                        'title': title,
                        'room_type': rtype,
                        'capacity_adults': cadults,
                        'capacity_children': ckids,
                        'price_per_night': price,
                        'is_active': True,
                        'description': f"{hotel.name}dagi {title}. Qulay krovat, smart TV, yuqori tezlikdagi internet va xususiy hammom bilan ta'minlangan.",
                    }
                )

            # Sample review
            first_room = hotel.rooms.first()
            if first_room and hcreated:
                # Create a sample completed booking for review
                past_checkin = timezone.localdate() - timezone.timedelta(days=10)
                past_checkout = timezone.localdate() - timezone.timedelta(days=7)
                booking = Booking.objects.create(
                    user=customer_user,
                    room=first_room,
                    check_in=past_checkin,
                    check_out=past_checkout,
                    adults=2,
                    children=0,
                    guest_name="Alisher Usmonov",
                    guest_phone="+998909876543",
                    nightly_price_snapshot=first_room.price_per_night,
                    total_price=first_room.price_per_night * 3,
                    status=BookingStatus.COMPLETED
                )
                BookingStatusLog.objects.create(
                    booking=booking,
                    old_status=BookingStatus.CONFIRMED,
                    new_status=BookingStatus.COMPLETED,
                    actor=manager_user,
                    note="Mijoz muvaffaqiyatli chiqib ketdi."
                )
                Review.objects.create(
                    hotel=hotel,
                    user=customer_user,
                    booking=booking,
                    rating=5,
                    comment="Ajoyib xizmat va tozalik! Xodimlar juda xushmuomala, xonalar keng va shinam. Hammaga tavsiya qilaman.",
                    is_visible=True
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded StayBook database!"))
