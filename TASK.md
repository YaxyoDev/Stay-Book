# StayBook — Hotel Booking System

> **TASK.md | Project Specification & Development Checklist**  
> **Stack:** Python 3.12+, Django 5.2 LTS / compatible stable release, Django Templates (MVT), PostgreSQL, HTML, CSS, JavaScript, Bootstrap 5, Gunicorn, Nginx, Ubuntu VPS.  
> **Muhim:** Django REST Framework, React, Vue, Next.js yoki alohida API frontend ishlatilmaydi. Barcha sahifalar server-side Django Templates orqali render qilinadi.

## 1. Loyiha maqsadi

**StayBook** — foydalanuvchilar turli mehmonxonalarni qidirishi, xona va sanalarni tanlashi, bron yaratishi va bron holatini kuzatishi mumkin bo‘lgan web-platforma. Mehmonxona menejeri o‘z mehmonxonasi, xonalari va bronlarini boshqaradi. Platforma administratori barcha mehmonxona va foydalanuvchilarni nazorat qiladi.

**MVP doirasi:** Bir nechta mehmonxona, bir nechta xona, ro‘yxatdan o‘tish, qidiruv/filtr, sanalar bo‘yicha mavjudlik, bron, menejer dashboard, mijoz kabineti va serverga deploy. **Onlayn to‘lov MVPga kirmaydi** — 'mehmonxonada to‘lash'.

### Maqsad mezonlari
- [ ] Har kim landing page va mehmonxona katalogini ochishi mumkin.
- [ ] Mijoz akkaunt ochib, bron yaratadi, o‘z bronlarini ko‘radi va qoidalarga muvofiq bekor qiladi.
- [ ] Bir xona bir-biriga kesishadigan sanalarda ikki marta bron qilinmaydi, hatto parallel so‘rovlarda ham.
- [ ] Manager faqat o‘z mehmonxonalarini va ularga tegishli bronlarni boshqaradi.
- [ ] Superuser moderation va umumiy monitoring qila oladi.
- [ ] Production serverda domen, HTTPS, statik/media fayllar va PostgreSQL ishlaydi.

## 2. Rollar va huquqlar

| Rol | Huquqlar |
|---|---|
| Visitor | Home, mehmonxona katalogi, filtrlar, detail va mavjudlikni ko‘rish |
| Customer | Visitor huquqlari + profil, bron yaratish, o‘z bronlarini ko‘rish/bekor qilish, review yozish |
| Hotel Manager | Customer huquqlari + faqat o‘z mehmonxonasi/xonalarini CRUD qilish, bronlarni tasdiqlash/rad etish, dashboard |
| Platform Admin | Django Admin orqali barcha obyektlar, menejer tayinlash, moderatsiya va audit |

- [ ] Custom User modelni **birinchi migrationdan oldin** yaratish (`AbstractUser`, `role`, `phone` va zarur maydonlar).
- [ ] `AUTH_USER_MODEL`ni boshidan sozlash.
- [ ] `LoginView`, `LogoutView`, `PasswordResetView` va email yuborish imkonini qo‘shish.
- [ ] Form, view va queryset darajasida ownership/authorization tekshirilsin; faqat tugmalarni yashirish yetarli emas.
- [ ] Manager rolini foydalanuvchi o‘zi tanlay olmasin; admin tayinlasin.

## 3. Texnologiyalar va arxitektura

- **Backend:** Django MVT, Django ORM, Class-Based/Function-Based Views, ModelForm, messages, auth, sessions, CSRF.
- **Frontend:** Django Template Language, HTML5, Bootstrap 5, qo‘shimcha CSS va zarur vanilla JavaScript.
- **DB:** PostgreSQL; lokalda ham PostgreSQL afzal.
- **Static:** `collectstatic`, WhiteNoise (sodda variant) yoki Nginx orqali static; production media Nginx + persistent disk / object storage.
- **Serving:** Gunicorn + Nginx + systemd, Ubuntu LTS VPS.
- **Tests:** Django `TestCase` + `TransactionTestCase` (DB locking/concurrency testlari uchun PostgreSQL).
- **Env:** `.env` orqali maxfiy sozlamalar; `.env` gitga kirmaydi.
- **Optional later:** Redis/Celery, online payment, i18n, email notifications.

### App struktura

```text
staybook/
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/
├── hotels/
├── bookings/
├── reviews/
├── dashboard/
├── templates/
│   ├── base.html
│   ├── includes/{navbar,footer,messages}.html
│   ├── accounts/
│   ├── hotels/
│   ├── bookings/
│   └── dashboard/
├── static/{css,js,img}/
├── media/                 # productionda persistent storage
├── tests/                 # yoki har app ichida tests/
├── requirements.txt
├── .env.example
├── .gitignore
├── manage.py
└── TASK.md
```

## 4. Ma’lumotlar bazasi

### 4.1 Accounts — `User`
- `id`, `username` (yoki email login strategiyasini boshida tanlash), `email` (unique), `first_name`, `last_name`, `phone`, `role` (`CUSTOMER`, `MANAGER`), `is_active`, `date_joined`.
- [ ] Profilni tahrirlash; parolni xavfsiz almashtirish.
- [ ] Bron ma’lumotlari user o‘chirilganda qanday saqlanishi (protect/anonymize) oldindan belgilansin.

### 4.2 Hotels — `Hotel`
- `id`, `manager` → User (FK), `name`, `slug` (unique), `description`, `city`, `address`, `latitude` (optional), `longitude` (optional), `stars` (1–5), `contact_phone`, `check_in_time`, `check_out_time`, `is_published`, `created_at`.
- [ ] Mehmonxona rasmi uchun `HotelImage`: `hotel`, `image`, `alt_text`, `sort_order`.
- [ ] `Amenity`: `name`, `icon` (optional); `Hotel.amenities` ManyToMany.

### 4.3 Rooms — `Room`
- `id`, `hotel` (FK), `number` (bir hotel ichida unique), `title`, `description`, `room_type` (`STANDARD`, `DELUXE`, `SUITE`), `capacity_adults`, `capacity_children`, `price_per_night` (`DecimalField`), `is_active`, `created_at`.
- [ ] `UniqueConstraint(fields=['hotel', 'number'])`.
- [ ] `RoomImage`: `room` (FK), `image`, `sort_order`.
- [ ] Narx manfiy bo‘lmasin, sig‘im musbat bo‘lsin.

### 4.4 Bookings — `Booking`
- `id` (UUID bo‘lsa URLni taxmin qilish qiyinroq), `user` (FK), `room` (FK), `check_in` (DateField), `check_out` (DateField), `adults`, `children`, `guest_name`, `guest_phone`, `nightly_price_snapshot` (`DecimalField`), `total_price` (`DecimalField`), `status` (`PENDING`, `CONFIRMED`, `CANCELLED`, `REJECTED`, `COMPLETED`), `created_at`, `updated_at`, `cancelled_at`.
- [ ] Bron yaratilganda tungi narx snapshot olinadi, keyinchalik xona narxi o‘zgarsa eski buyurtma narxi o‘zgarmaydi.
- [ ] Tarixiy ma’lumotlarni saqlash uchun room/bookings o‘chirilishi siyosatini belgilang (`PROTECT` yoki soft-delete).
- [ ] Status o‘zgarishi uchun alohida `BookingStatusLog` (`booking`, `old_status`, `new_status`, `actor`, `created_at`, `note`).

### 4.5 Reviews — `Review`
- `id`, `hotel` (FK), `user` (FK), `booking` (OneToOne), `rating` (1–5), `comment`, `created_at`, `is_visible`.
- [ ] Review faqat shu userning `COMPLETED` bronidan keyin yozilsin.
- [ ] Bitta bron uchun bitta review.

## 5. Bronlash qoidalari — eng muhim modul

**Sana oralig‘i:** `[check_in, check_out)`; chiqish sanasi band kun emas. Masalan, 10–13 noyabr bron qilingan xona uchun 13 noyabr kuni yangi bron boshlanishi mumkin.

**Kesishish formulasi:** `existing.check_in < new_check_out AND existing.check_out > new_check_in`.

- [ ] `check_in >= bugungi sana`; `check_out > check_in`.
- [ ] Minimal bron: 1 kecha; maksimum (masalan) 30 kecha — konfiguratsiya.
- [ ] Mehmonlar soni xona sig‘imidan oshmasin.
- [ ] Faqat `is_active=True` xona va `is_published=True` hotel bron qilinsin.
- [ ] `PENDING` va `CONFIRMED` statusidagi bronlar xonani band qiladi; `CANCELLED`, `REJECTED` band qilmaydi. `COMPLETED` tarixiy bandlikni ifodalaydi (o‘tgan kunlar uchun).
- [ ] **Muhim concurrency:** bronni yakunlashda `transaction.atomic()` ichida tegishli **Room qatorini `select_for_update()` bilan lock qilish**, mavjud band bronlarni qayta tekshirish va so‘ng bron yaratish. PostgreSQLda test qilish; oddiy `exists()` + `create()` lock'siz race conditionga olib keladi. Har qanday bron yaratish yo‘li bir xil lock ketma-ketligidan foydalansin.
- [ ] Mijoz POST yuborgan narxga ishonilmasin: narx serverda `Decimal` bilan hisoblanadi: `(check_out - check_in).days * room.price_per_night`.
- [ ] Cancel policy: masalan, `check_in`dan 24 soat oldingacha (aniq qoida saytda ko‘rsatilsin); MVPda bu qoida sozlanadigan bo‘lishi mumkin.
- [ ] Menejer bronni tasdiqlashi/rad etishi mumkin; faqat o‘z mehmonxonasida.
- [ ] Double-submit oldini olish: POST/Redirect/GET va yaratish uchun idempotency token (yoki bir martalik form nonce) qo‘llash tavsiya etiladi.

## 6. Sahifalar va URL reja

| URL | Sahifa | Kirish |
|---|---|---|
| `/` | Landing page, qidiruv formasi, mashhur mehmonxonalar | Public |
| `/hotels/` | Mehmonxona katalogi, search/filter/sort/pagination | Public |
| `/hotels/<slug:slug>/` | Mehmonxona detali, galereya, xonalar, reviews | Public |
| `/rooms/<int:pk>/` | Xona tafsiloti, narx, mavjudlik | Public |
| `/accounts/register/` | Ro‘yxatdan o‘tish | Visitor |
| `/accounts/login/` | Login | Visitor |
| `/accounts/logout/` | Logout POST | Auth |
| `/accounts/profile/` | Profil ma’lumotlari | Auth |
| `/bookings/create/<int:room_id>/` | Bron formasi (GET/POST) | Customer |
| `/bookings/` | Mening bronlarim, status filter | Customer |
| `/bookings/<uuid:pk>/` | Bron tafsiloti | Egasi / manager |
| `/bookings/<uuid:pk>/cancel/` | Bekor qilish (POST) | Egasi |
| `/dashboard/` | Hotel manager overview | Manager |
| `/dashboard/hotels/` | O‘z mehmonxonalarini boshqarish | Manager |
| `/dashboard/rooms/` | O‘z xonalarini CRUD | Manager |
| `/dashboard/bookings/` | Kelgan bronlarni filtrlash/tasdiqlash | Manager |
| `/admin/` | Django Admin | Superuser |

### Katalog qidiruv/filtr
- [ ] `q` — hotel nomi/joylashuv.
- [ ] `city`, `min_price`, `max_price`, `stars`, `amenity`.
- [ ] `check_in`, `check_out`, `adults`, `children` bo‘yicha bo‘sh xonalar.
- [ ] Sort: `price_asc`, `price_desc`, `rating_desc`, `newest`.
- [ ] Pagination (masalan 9 yoki 12 ta hotel per page).
- [ ] URL query parametrlar filtrlash va paginationda saqlansin.
- [ ] `select_related`/`prefetch_related` bilan N+1 query optimallashtirilsin.

## 7. Frontend / UI talablari

### Dizayn
- [ ] Professional, responsive, minimalistik hotel/travel uslubi.
- [ ] Brend: **StayBook**; palette: to‘q ko‘k, oq, turkuaz aksent (moslashtirish mumkin).
- [ ] Mobile (360px+), tablet va desktop mosligi.
- [ ] Bootstrap navbar, footer, toast/alert, cards, forms, pagination, modal.
- [ ] Barcha input va xatolik xabarlari o‘zbek tilida; keyin i18n qilishga tayyor strukturada.
- [ ] Accessible label, alt matn, klaviatura navigatsiyasi, focus indicator.

### Jamoatchilik sahifalari
- [ ] Home: hero + qidiruv, featured destinations, hotels carousel/cards, qanday ishlaydi.
- [ ] Hotels listing: left filter/sidebar (mobile offcanvas), grid/list toggle (optional), hotel cards.
- [ ] Hotel detail: image gallery, facilities, map link, reviews, mavjud xonalar.
- [ ] Room detail: katta rasm, tur, maksimal mehmonlar, narx, sana formasi.
- [ ] Booking form: sanalar, mehmonlar, aloqa, narx breakdown va tasdiqlash.
- [ ] Booking confirmation: booking ID, sanalar, hotel, room, status, yakuniy narx.
- [ ] Profile: kontaktlar, bronlar tarixi, cancel action.

### Menejer Dashboard
- [ ] KPI cards: bugungi check-in, yangi pending bronlar, band xonalar, jami bronlar.
- [ ] Bookings table: qidiruv, status, sanalar va hotel bo‘yicha filter.
- [ ] Xona rasmlari, narxi va faol holatini o‘zgartirish.
- [ ] Bron confirmation/rejection workflow va status log.
- [ ] Revenue statistikasi: MVPda **bron qiymatlari** deb belgilang, real to‘langan tushum emas.

## 8. Django Admin
- [ ] `list_display`, `search_fields`, `list_filter`, `readonly_fields`.
- [ ] Hotel, Room, Booking, Review adminlar.
- [ ] HotelImage va RoomImage inline.
- [ ] Bron sanalari, snapshot narx va status log nazorati.
- [ ] Admin tomonidan to‘g‘ridan-to‘g‘ri bron yaratish ham umumiy concurrency/validation qoidalarini buzmasin (yoki admin create ruxsatini cheklash).

## 9. Security & data validation

- [ ] CSRF token barcha POST formalarda.
- [ ] LoginRequiredMixin / permission mixin / ownership queryset.
- [ ] `next` redirect faqat safe URLga.
- [ ] User input server-side `Form` / `ModelForm.clean()` orqali tekshirilsin.
- [ ] `SECRET_KEY`, DB password, email credentials `.env`da.
- [ ] `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, HTTPS/security cookie sozlamalari.
- [ ] Upload uchun ruxsatli format, hajm limiti, xavfsiz filename handling; public media fayllarni bajariladigan kod sifatida bermaslik.
- [ ] Django autoescaping, ORM parametrizatsiyasi; xavfli `mark_safe` yoki raw SQL ishlatmaslik.
- [ ] Login brute-force himoyasi/rate limiting (zarur paket bilan) va logging.
- [ ] Shaxsiy ma’lumotlarni minimal yig‘ish, maxfiylik siyosati sahifasi.

## 10. Test senariylari

- [ ] Register/login/logout/password reset ishlaydi.
- [ ] Customer manager dashboardga kira olmaydi.
- [ ] Manager boshqa manager hotel/room/bookings ma’lumotini ko‘ra olmaydi yoki o‘zgartira olmaydi.
- [ ] `check_out <= check_in` xato beradi.
- [ ] O‘tgan sanalar reject.
- [ ] Xona sig‘imi oshsa reject.
- [ ] 10–13-noyabr band bo‘lsa 11–12-noyabr reject; 13–15-noyabr ruxsat.
- [ ] Parallel ikki mijoz bir xona/bir vaqtga bron yuborsa, faqat bittasi muvaffaqiyatli bo‘ladi.
- [ ] Cancelled/rejected bron bandlikni saqlamaydi.
- [ ] Client soxta narx POST qilsa server narxi ishlatiladi.
- [ ] Reviewni faqat yakunlangan bron egasi qila oladi.
- [ ] File upload, sahifalash, filtr, 404/403 template, oddiy accessibility va mobile layout ishlaydi.

## 11. Bosqichma-bosqich development plan

### Phase 1 — Foundation
- [ ] Repo va `.gitignore`, virtual environment, Django project/apps.
- [ ] PostgreSQL va settings/.env.
- [ ] Custom User model va birinchi migration.
- [ ] `base.html`, navbar/footer, static, Bootstrap, flash messages.

### Phase 2 — Authentication
- [ ] Register/login/logout, reset password, profile.
- [ ] Permission mixin va manager role workflow.

### Phase 3 — Hotels & Rooms
- [ ] Hotel/Amenity/Room/Image modellari va migration.
- [ ] Manager CRUD, image upload, Django Admin.
- [ ] Public hotel listing/detail, room detail.

### Phase 4 — Search & Availability
- [ ] Search/filter/sort/pagination.
- [ ] Sana + sig‘im bo‘yicha bo‘sh xonalar.
- [ ] UI filter form va invalid range xatolari.

### Phase 5 — Bookings
- [ ] Booking, status log, rezervatsiya servisi.
- [ ] Transaction + room-level locking.
- [ ] Customer bookings, detail, cancel.
- [ ] Manager approve/reject, permission checks.

### Phase 6 — Reviews & Dashboard
- [ ] Completed booking review, rating aggregation.
- [ ] Manager dashboard, statistikalar, bronlar jadvali.

### Phase 7 — Quality & Deployment
- [ ] Testlar (ayniqsa concurrency), error pages, responsive QA.
- [ ] Security checklist, logging, DB indexes, query profiling.
- [ ] Ubuntu VPS, PostgreSQL, Gunicorn, systemd, Nginx, SSL.
- [ ] Backups va restore test.

## 12. VPS deployment checklist

- [ ] Ubuntu LTS server; `deploy` user, SSH key, firewall (22/80/443).
- [ ] Python virtualenv, dependencies va PostgreSQL user/database.
- [ ] Source Git orqali, `.env` serverda.
- [ ] `python manage.py migrate`.
- [ ] `python manage.py collectstatic --noinput`.
- [ ] `python manage.py check --deploy` va ogohlantirishlarni ko‘rib chiqish.
- [ ] Gunicorn systemd service; Nginx reverse proxy.
- [ ] Nginx static/media konfiguratsiyasi, upload hajmi va media volume.
- [ ] Domen DNS, Let's Encrypt TLS, HTTP → HTTPS.
- [ ] `DEBUG=False`, secure session/CSRF cookies va allowed hosts.
- [ ] Superuser yaratish va demo seed data.
- [ ] PostgreSQL avtomatik backup, off-server saqlash va tiklash sinovi.
- [ ] Log rotation, monitoring, restart policy.

## 13. Definition of Done — yakunlash mezoni

Loyiha **tayyor** hisoblanadi, qachonki:

- [ ] Visitor hotelni topishi, sana tanlashi va bo‘sh xonalarni ko‘ra oladi.
- [ ] Customer akkaunt bilan bron yaratadi, tarixini ko‘radi va bekor qiladi.
- [ ] Manager faqat o‘z obyektlarini boshqaradi.
- [ ] Double booking parallel so‘rovlarda ham oldi olingan.
- [ ] Muhim biznes qoidalar avtomatlashtirilgan test bilan tekshirilgan.
- [ ] Mobil interfeys ishlaydi.
- [ ] HTTPS domen orqali serverda ishga tushgan.
- [ ] README: o‘rnatish, `.env.example`, migratsiya, test, deploy va demo credentials yo‘riqnomasi.

## 14. MVPdan keyingi imkoniyatlar (hozir shart emas)

- [ ] O‘zbek / rus / ingliz tarjimalar.
- [ ] Email yoki Telegram booking notification.
- [ ] Click / Payme orqali to‘lov va webhook xavfsizligi.
- [ ] QR-code bron tasdig‘i va invoice PDF.
- [ ] Xonalar bo‘yicha bandlik kalendari.
- [ ] Discount/coupon, seasonal pricing, promo codes.
- [ ] Hotel manager uchun bir nechta xodim va ichki rollar.
- [ ] Celery/Redis bilan scheduled reminders.
- [ ] Advanced PostgreSQL exclusion constraint yoki inventory modelga o‘tish (talab kengaysa).

---

**Ishni boshlash tartibi:** Phase 1 → Phase 2 → Phase 3 ... . Har bir phase uchun alohida commit qiling. Birinchi bo‘lib custom User va permission architecture ni ishlab chiqing; keyin model, form, view, template, URL va testlarni ketma-ket yozing.

### !!! DIQQAT !!! ###

## 🎨 UI/UX Design — Figma

Loyihaning tayyor UI/UX dizayni `stitch_task_and_reading_tracker/` papkasida joylashgan.

### Talablar
- Barcha sahifalar ushbu papkadagi Figma UI dizayniga asoslanib yaratilishi kerak.
- Dizayndagi ranglar, shriftlar, tugmalar, kartochkalar, ikonlar va boshqa elementlar imkon qadar aynan saqlansin.
- Frontend **Django Templates + HTML + CSS + JavaScript** yordamida ishlab chiqilsin.
- Barcha sahifalar responsive bo‘lishi kerak.
- Dizaynni o‘zboshimchalik bilan o‘zgartirish mumkin emas.
- Figma dizayni loyihaning asosiy UI/UX manbasi (*Single Source of Truth*) hisoblanadi.

**Muhim:** Kod yozishni boshlashdan oldin `stitch_task_and_reading_tracker/` papkasidagi barcha mavjud dizayn fayllarini o‘rganib chiqish va frontendni shu dizaynlarga mos ravishda yaratish shart.
