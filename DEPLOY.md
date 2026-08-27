# IDEAL SETKA — Render'ga 0 dan joylash (24/7 reja)

Bu qo'llanma botni Render'ga birinchi marta joylashtirish va uni **doimiy (24/7)**
ishlatib turish uchun to'liq qadamlarni o'z ichiga oladi.

## 0-qadam — kerakli narsalar

- Telegram bot tokeni (BotFather'dan `/newbot` orqali olingan)
- GitHub hisobi (bepul) — Render kodni shu yerdan oladi
- Bank kartasi — Render'ning **pullik (Starter) tarifi** uchun (24/7 ishlashi shart)

## 1-qadam — kodni GitHub'ga yuklash

**Eng oson yo'l (kod bilishingiz shart emas):**
1. https://github.com sahifasida ro'yxatdan o'ting (agar hisobingiz bo'lmasa)
2. Yuqori o'ngdagi **+** → **New repository** → nom bering (masalan `ideal-setka-bot`) → **Public** yoki **Private** → **Create repository**
3. Ochilgan sahifada **"uploading an existing file"** havolasini bosing
4. Kompyuteringizda ZIP faylni oching (arxivdan chiqaring) va **ideal_setka_replit_bot** papkasi ichidagi barcha fayl/papkalarni birdaniga sudrab (drag & drop) shu sahifaga tashlang
5. Pastda **Commit changes** tugmasini bosing

> Git bilan ishlay olsangiz, albatta oddiy `git init && git add . && git commit -m "init" && git push` yo'li ham bo'ladi.

## 2-qadam — Render'da hisob ochish va loyihani ulash

1. https://render.com → **Get Started** → GitHub hisobingiz orqali kiring
2. Render'ga GitHub repolaringizga kirish huquqini bering (yoki faqat yangi repoga ruxsat bering)
3. Dashboard'da **New +** → **Blueprint** ni tanlang
4. Ro'yxatdan yaratgan repongizni (`ideal-setka-bot`) tanlang

Loyihada tayyor `render.yaml` fayli bor — Render uni avtomatik o'qib, kerakli
xizmatni (web service, doimiy disk, health check) o'zi sozlaydi. Sizdan faqat
quyidagi maxfiy qiymatlarni kiritish so'raladi:

| O'zgaruvchi | Qiymat |
|---|---|
| `BOT_TOKEN` | BotFather'dan olingan token |
| `ADMIN_IDS` | Admin Telegram ID'lar (bo'sh qoldirsangiz kodga o'rnatilgan 4 ta standart admin ishlaydi) |
| `WEBAPP_URL` | Hozircha **bo'sh qoldiring** — 4-qadamda to'ldiramiz |
| `ANTHROPIC_API_KEY` | Ixtiyoriy (AI yordamchi uchun) |

**Apply** / **Create New Resources** tugmasini bosing.

## 3-qadam — tarifni tekshiring (24/7 uchun MUHIM)

`render.yaml`da xizmat allaqachon **Starter** tarifga sozlangan (Free emas).
Agar Render sizdan to'lov ma'lumotini so'rasa — kartangizni kiriting va tasdiqlang.

> ⚠️ Agar tasodifan **Free** tarifga tushib qolsangiz: Settings → Instance Type →
> **Starter** ($7/oy dan boshlab) ni tanlang. Free tarifda server 15 daqiqa
> harakatsizlikdan keyin uxlab qoladi va bot vaqtincha javob bermay qoladi.

Birinchi deploy 2-5 daqiqa davom etadi. Tugagach, xizmat sahifasida yuqorida
`https://ideal-setka-bot-XXXX.onrender.com` kabi ochiq URL ko'rinadi.

## 4-qadam — WEBAPP_URL'ni to'ldirish

1. Yuqoridagi URL'ni nusxalang va oxiriga `/app/` qo'shing:
   `https://ideal-setka-bot-XXXX.onrender.com/app/`
2. Render dashboard → xizmatingiz → **Environment** → `WEBAPP_URL` qatoriga shu manzilni kiriting → **Save Changes**
3. Render avtomatik qayta deploy qiladi (1-2 daqiqa)

## 5-qadam — tekshirish

- Brauzerda `https://.../health` ochilsa `{"status":"ok"}` chiqishi kerak
- Telegram'da botingizga `/start` yozing — menyu chiqishi kerak
- **🛒 Mini App / Buyurtma** tugmasini bosib Mini App ochilishini tekshiring
- `/admin` yozib (admin ID'ingiz bilan) admin panel ochilishini tekshiring

Hammasi ishласа — bot tayyor va ishlab turibdi. ✅

---

## 24/7 ishlashi bo'yicha muhim eslatmalar

1. **Tarif doim Starter (yoki undan yuqori) bo'lishi kerak.** Free tarifda
   bot uxlab qoladi — savdo boti uchun bu yaroqsiz.
2. **To'lov muddati tugamasin.** Karta muddati tugasa yoki mablag' yetmasa,
   Render xizmatni to'xtatadi. Kartangizni yangilab turing.
3. **Doimiy disk (persistent disk) allaqachon ulangan** (`render.yaml` orqali) —
   bazadagi mahsulot, buyurtma va chek ma'lumotlari har safar qayta deploy
   qilinganda **o'chib ketmaydi**. Bu juda muhim: disk bo'lmasa, har yangilanishda
   butun baza (buyurtmalar tarixi ham) yo'qolib qoladi.
4. **Qayta deploy paytida qisqa uzilish bo'ladi** (disk ulangan xizmatlarda bu
   normal holat, bir necha soniya-daqiqa). Kunlik ishlashga ta'sir qilmaydi —
   faqat siz kodni yangilab push qilgan paytda yuz beradi.
5. **Kodni o'zgartirmasdan** ko'p narsani boshqarish mumkin: narx, mahsulot,
   rasm, texnik rejim — hammasi `/admin` panel orqali, qayta deploy shart emas.
6. **Loglarni kuzatish**: muammo bo'lsa, Render dashboard → xizmatingiz →
   **Logs** bo'limidan xatolikni ko'rish mumkin.
7. Render doimiy diskni **har 24 soatda avtomatik zaxira (snapshot)** qiladi —
   qo'shimcha backup sozlash shart emas, lekin muhim bo'lsa buni ham bilib qo'ying.

## Agar keyinchalik kodni yangilamoqchi bo'lsangiz

GitHub repongizga yangi versiyani yuklasangiz (yoki push qilsangiz), Render
`autoDeploy: true` sozlamasi tufayli **avtomatik ravishda qayta deploy qiladi** —
qo'shimcha amal talab qilinmaydi.
