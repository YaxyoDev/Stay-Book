# StayBook — Mehmonxonalarni bron qilish tizimi (Hotel Booking System)

StayBook — foydalanuvchilar O'zbekiston bo'ylab turli mehmonxonalarni qidirishi, sana va xona toifalarini tanlashi, bron yaratishi va buyurtma holatini kuzatishi mumkin bo‘lgan to‘liq server-side veb-platforma. Mehmonxona menejerlari o‘z mehmonxonalari, xonalari va kelib tushgan buyurtmalarini maxsus boshqaruv paneli (Dashboard) orqali boshqaradi.

---

## 🛠 Texnologiyalar to'plami (Tech Stack)

- **Backend:** Python 3.12+, Django 5.2 LTS (MVT arxitekturasi)
- **Ma'lumotlar bazasi:** PostgreSQL 17 (psycopg 3 drayveri) va mahalliy testlar uchun SQLite fallback
- **Frontend:** Django Templates, HTML5, CSS3, JavaScript, Tailwind CSS (Figma design tizimi asosida), Google Fonts (Manrope, Inter, Material Symbols)
- **Statik fayllar:** WhiteNoise, Django Staticfiles
- **Deploy:** Gunicorn, Nginx, Systemd, Ubuntu VPS, Let's Encrypt SSL

---

## 🔑 Demo hisob ma'lumotlari (Credentials)

Bazada oldindan yaratilgan namunaviy foydalanuvchilar:

| Rol | Login / Username | Parol | Huquqlar |
|---|---|---|---|
| **Superuser / Platform Admin** | `admin` | `admin1234` | Barcha ma'lumotlar, Django Admin, to'liq boshqaruv |
| **Mehmonxona Menejeri** | `manager1` | `manager1234` | O'z mehmonxonalari, xonalari, buyurtmalarni tasdiqlash/rad etish |
| **Oddiy Mijoz (Customer)** | `customer1` | `customer1234` | Bron yaratish, o'z bronlarini ko'rish/bekor qilish, sharh yozish |

---

## 🚀 Loyihani lokal o'rnatish va ishga tushirish

### 1. Repozitoriyani klonlash va virtual muhit yaratish
```bash
git clone <repo-url>
cd hotel-booking

# Virtual muhit yaratish
python -m venv .venv

# Virtual muhitni faollashtirish
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate
```

### 2. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 3. Konfiguratsiya fayli (.env)
`.env.example` faylidan nusxa olib `.env` faylini yarating:
```bash
cp .env.example .env
```
`.env` faylidagi sozlamalar:
```env
DEBUG=True
SECRET_KEY=your-secure-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1
USE_SQLITE=True
# PostgreSQL ishlatish uchun USE_SQLITE=False qilib quyidagilarni to'ldiring:
DB_NAME=staybook_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 4. Ma'lumotlar bazasi migratsiyalari
```bash
python manage.py migrate
```

### 5. Namunaviy ma'lumotlarni yuklash (Seed Data)
Barcha shaharlar (Toshkent, Samarqand, Buxoro, Xiva, Zomin), mehmonxonalar, xonalar, qulayliklar va foydalanuvchilarni bazaga avtomatik kiritish:
```bash
python manage.py seed_data
```

### 6. Testlarni ishga tushirish
```bash
# Barcha 27 ta unit va concurrency testlarni yurgizish:
python manage.py test
```

### 7. Serverni ishga tushirish
```bash
python manage.py runserver
```
Brauzerda oching: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🛡️ Muhim biznes-mantiq va Concurrency himoyasi

1. **Sana kesishishi formulasi:**  
   `existing.check_in < new_check_out AND existing.check_out > new_check_in`  
   Chiqish sanasi band kun hisoblanmaydi (masalan, 10–13 noyabr kunlariga bron qilingan xonaga 13–15 noyabr kunlarida yangi mehmon kirishi mumkin).

2. **Race condition va Double Booking oldini olish:**  
   Bron yaratish jarayoni `transaction.atomic()` blokida bajariladi va xona qatori `Room.objects.select_for_update().get(id=room_id)` orqali qulflanadi (row-level DB lock). Bu parallel mijozlar bir vaqtning o'zida bron yuborgan taqdirda ham ikkinchi so'rov navbatda kutib, xona bandligini aniqlashini kafolatlaydi.

3. **Mijoz yuborgan narxga ishonilmaydi:**  
   Barcha hisob-kitoblar faqat serverda `Decimal` formatida snapshot qilib saqlanadi: `nights * room.price_per_night`. Kelgusida xona narxi o'zgarsa ham, o'tmishdagi buyurtma narxi o'zgarmasdan saqlanadi.

4. **Avtorizatsiya va Cheklovlar:**  
   - Yangi ro'yxatdan o'tgan har bir foydalanuvchi faqat `CUSTOMER` bo'ladi. `MANAGER` rolini faqat Platform Admin tayinlashi mumkin.
   - Menejer faqat o'ziga tegishli bo'lgan mehmonxonalar, xonalar va bronlarni ko'radi va boshqaradi.

---

## 🌐 Production VPS Deployment (Ubuntu LTS)

### 1. Gunicorn Systemd xizmati (`/etc/systemd/system/staybook.service`)
```ini
[Unit]
Description=StayBook Gunicorn Daemon
After=network.target

[Service]
User=deploy
Group=www-data
WorkingDirectory=/var/www/staybook
ExecStart=/var/www/staybook/.venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/staybook.sock config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Nginx konfiguratsiyasi (`/etc/nginx/sites-available/staybook`)
```nginx
server {
    server_name staybook.uz www.staybook.uz;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/staybook/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias /var/www/staybook/media/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/staybook.sock;
    }

    listen 80;
}
```

### 3. SSL sertifikat (Certbot)
```bash
sudo certbot --nginx -d staybook.uz -d www.staybook.uz
```

---

## 📂 Sahifalar va URL xaritasi

- `/` — Bosh sahifa (Landing page, qidiruv widgeti, mashhur shaharlar, tavsiya etilgan mehmonxonalar)
- `/hotels/` — Mehmonxonalar katalogi (Qidiruv, filtrlar: shahar, narx, yulduz, qulayliklar, saralash, sahifalash)
- `/hotels/<slug:slug>/` — Mehmonxona sahifasi (Galereya, qulayliklar, xonalar ro'yxati, sharhlar)
- `/rooms/<int:pk>/` — Xona tafsiloti va sanani tekshirish
- `/accounts/register/` — Ro'yxatdan o'tish
- `/accounts/login/` — Tizimga kirish
- `/accounts/logout/` — Chiqish (POST)
- `/accounts/profile/` — Shaxsiy profil va parolni almashtirish
- `/bookings/` — Mening bronlarim (Faol, yakunlangan, bekor qilingan tablari)
- `/bookings/create/<int:room_id>/` — Bron shakllantirish formasi
- `/bookings/<uuid:pk>/` — Bron tasdiqnomasi (Voucher)
- `/bookings/<uuid:pk>/cancel/` — Bronni bekor qilish (POST)
- `/dashboard/` — Menejer umumiy ko'rsatkichlari (KPI kartochkalar, statistikalar)
- `/dashboard/hotels/` — Menejer mehmonxonalari ro'yxati va yangi ob'yekt qo'shish
- `/dashboard/rooms/` — Xonalarni boshqarish (CRUD va holatni o'zgartirish)
- `/dashboard/bookings/` — Kelgan buyurtmalar jadvali va tasdiqlash/rad etish
- `/admin/` — Django boshqaruv paneli (Platform Admin)
