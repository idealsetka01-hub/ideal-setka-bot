# IDEAL SETKA — Telegram Bot + Mini App

To‘liq ishlaydigan Telegram Bot + Telegram Mini App: 8 ta kategoriya, buyurtma
oqimi (bot ichida va Mini App orqali), to‘lov tizimi (QR/CLICK/PAYME),
admin panel, texnik rejim, kategoriya rasmlari va AI yordamchi.

## Loyiha tuzilishi

```
project/
├── main.py                # Bot polling + FastAPI serverni bitta processda ishga tushiradi
├── server.py               # FastAPI backend — Mini App uchun REST API
├── config.py               # Sozlamalar, admin ID'lar, to'lov ma'lumotlari
├── bot/
│   ├── bot_instance.py       # Bot obyektini bot va server o'rtasida ulashish
│   ├── keyboards.py          # Barcha inline klaviaturalar
│   ├── states.py            # FSM holatlari
│   ├── orders.py            # Buyurtmani yakunlash/adminlarga xabar (bot va webapp uchun umumiy)
│   ├── utils.py             # Formatlash yordamchilari
│   └── handlers/
│       ├── start.py          # /start
│       ├── catalog.py         # Kategoriya va mahsulotlarni ko'rsatish
│       ├── order.py          # Miqdor → ism/telefon/manzil → to'lov → chek
│       ├── admin.py          # Admin panel: mahsulot, rasm, texnik rejim, buyurtmalar
│       ├── contact.py         # Aloqa bo'limi
│       └── ai.py            # AI yordamchi (erkin matn — tugma shart emas)
├── database/
│   ├── db.py                # SQLite sxema, ulanish, seed
│   ├── models.py             # CRUD funksiyalar
│   └── products_data.py       # Boshlang'ich mahsulot ma'lumotlari (faqat bo'sh bazada ishlatiladi)
├── webapp/
│   ├── index.html            # Mini App
│   ├── style.css
│   └── app.js
├── static/products/           # Ixtiyoriy — lokal rasm fayllari uchun
├── requirements.txt
├── .env.example
├── .gitignore
├── replit.nix / .replit
└── README.md
```

## O‘rnatish (lokal / Replit / Render)

```bash
pip install -r requirements.txt
cp .env.example .env   # BOT_TOKEN va boshqa qiymatlarni to'ldiring
python main.py
```

`main.py` bitta processda ikkalasini birga ishga tushiradi:
- Telegram bot (aiogram, long polling)
- FastAPI server (Mini App uchun, `PORT` o'zgaruvchisida ko'rsatilgan portda)

### Replit

Secrets bo‘limiga: `BOT_TOKEN`, `ADMIN_IDS`, `WEBAPP_URL`, `ANTHROPIC_API_KEY` (ixtiyoriy).
"Run" tugmasi bosilganda `.replit` fayldagi buyruq avtomatik ishga tushadi.

### Render

- **Web Service** turini tanlang (Background Worker emas — chunki portni tinglashi kerak).
- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Environment Variables bo‘limiga `.env.example` dagi kalitlarni kiriting.
- `WEBAPP_URL` ni Render domeningizga qarab `https://<app-nomi>.onrender.com/app/` deb belgilang va shu URL’ni botga (`WEBAPP_URL`) bering.
- ⚠️ Bepul (Free) tarifda server 15 daqiqa harakatsizlikdan so‘ng "uxlab qoladi" — bot va Mini App 24/7 ishlashi uchun pullik (Starter va undan yuqori) tarif tavsiya etiladi.

## Kategoriyalar

1. YO‘L SETKA
2. SETKA RABITSA
3. G‘ISHT SETKA
4. SUVOQ SETKA
5. QUSH SETKA
6. TIKON SIM
7. ECO ZABOR — standart 10 metrlik rulon, miqdor so‘ralmaydi (avtomatik 1 rulon)
8. 3D ZABOR

Mahsulotlar bot birinchi marta ishga tushganda SQLite bazasiga yoziladi va
qayta ishga tushirilganda **takrorlanmaydi** (baza bo'sh bo'lgandagina seed ishlaydi).

## Buyurtma oqimi (bot va Mini App uchun bir xil natija)

1. **Bot orqali**: kategoriya → mahsulot → miqdor (faqat butun son: 1/2/5/10
   yoki qo‘lda kiritish) → ism/telefon/manzil → to‘lov usuli.
2. **Mini App orqali**: kategoriya → mahsulot → savatga qo‘shish (bir nechta
   mahsulot qo‘shish mumkin) → savat → ism/telefon/manzil → to‘lov usuli →
   buyurtmani tasdiqlash.
3. To‘lov usullari — barchasi online: **YAGONA QR-KOD → CLICK → PAYME**.
   To‘lov havolasi/QR ko‘rsatiladi → foydalanuvchi to‘lovni amalga
   oshiradi → chekni rasm qilib yuboradi (Mini App’dan buyurtma bergan
   bo‘lsa ham, chekni **bot chatida** yuboradi) → shundan keyin buyurtma
   barcha 4 adminga (matn + chek rasmi bilan) yuboriladi.
4. Har bir buyurtmaga unique kod beriladi: `#IS-000001`.
5. Har bir mahsulot sahifasida: `🚚 Yetkazib berish: Yetkazish narxlari kelishilgan holatda.`

## Admin imkoniyatlari

`/admin` — admin panelni ochadi:
- 📋 Mahsulotlar ro‘yxati
- ➕ Mahsulot qo‘shish (kategoriya → razmer → narx → birlik)
- 🖼 Kategoriya rasmi yuklash
- 🔧 Texnik rejim: yoqish/o‘chirish (SQLite `settings` jadvalida saqlanadi)
- 🌐 Mini App: yoqish/o‘chirish
- 📦 So‘nggi buyurtmalar
- 🧾 So‘nggi cheklar

Qo‘shimcha komandalar:
- `/products` — barcha faol mahsulotlar
- `/editprice <id> <yangi_narx>`
- `/editname <id> <yangi_nom>`
- `/delproduct <id>` — o‘chirmaydi, faqat `active=0` qiladi

Barcha admin funksiyalari faqat `config.py`dagi (yoki `ADMIN_IDS` env) ro‘yxatidagi
Telegram ID’lar uchun ishlaydi (standart: 8309612083, 803489469, 7671188664, 545524303).

## Texnik rejim

`/admin` panelidan yoqilganda (SQLite `settings.technical_mode`):
- Bot: `/start` va barcha tugmalar texnik xabar ko‘rsatadi, buyurtma/chek qabul qilinmaydi.
- Mini App: barcha `/api/*` so‘rovlari 503 bilan texnik xabar qaytaradi, frontend shu xabarni ko‘rsatadi.

`webapp_enabled` sozlamasi orqali Mini App’ni alohida ham o‘chirish mumkin
(bot o‘zi ishlashda davom etadi, faqat Mini App yopiladi).

## AI Yordamchi

Alohida tugma yoki komanda **shart emas** — botga yuborilgan har qanday erkin
matn xabar (boshqa aniq bosqichga — masalan ism/telefon kiritish — to‘g‘ri
kelmasa) avtomatik AI yordamchiga yo‘naltiriladi.

- AI **butun mahsulot bazasini** (barcha 8 kategoriya, barcha narx/razmerlar)
  bilib turadi va faqat shu ma’lumotlarga asoslanib javob beradi.
- AI **faqat IDEAL SETKA mahsulotlari va kompaniya mavzusida** javob beradi —
  boshqa mavzudagi savollarga (masalan umumiy bilim, boshqa sohalar) javob
  bermaydi va foydalanuvchini setka mavzusidagi savollarga yo‘naltiradi.
- `ANTHROPIC_API_KEY` berilmasa, oddiy kalit-so‘z qidiruvi rejimida ishlaydi
  (baribir mahsulot va narxlarni topib beradi, faqat javob "sun'iy intellekt"
  darajasida bo‘lmaydi).

## Baza jadvallari

`users`, `categories`, `products`, `orders`, `order_items`, `receipts`, `settings`.

## Eslatma

Bot tokeni, API kalitlar va boshqa maxfiy ma’lumotlar ushbu loyihaga yozilmagan —
ularni faqat `.env` yoki Replit/Render Secrets orqali kiriting.
