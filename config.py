# -*- coding: utf-8 -*-
"""Butun loyiha uchun umumiy sozlamalar. Maxfiy qiymatlar faqat .env orqali beriladi."""
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ideal_setka.db")
# DATABASE_URL sqlite:///name.db formatida beriladi -> aiosqlite uchun fayl nomini ajratib olamiz
DB_PATH = DATABASE_URL.split("sqlite:///")[-1] if "sqlite:///" in DATABASE_URL else "ideal_setka.db"

WEBAPP_PORT = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8000")))

# AI yordamchi uchun ixtiyoriy
AI_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")

# Standart 4 ta admin. ADMIN_IDS .env orqali ustidan yozilishi mumkin (vergul bilan ajratilgan).
_DEFAULT_ADMIN_IDS = [8309612083, 803489469, 7671188664, 545524303]


def _load_admin_ids():
    raw = os.getenv("ADMIN_IDS", "")
    if not raw.strip():
        return list(_DEFAULT_ADMIN_IDS)
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.append(int(part))
    return ids or list(_DEFAULT_ADMIN_IDS)


ADMIN_IDS = _load_admin_ids()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ---- Texnik rejim xabari ----
TECH_TEXT = (
    "🔧 <b>TEXNIK ISHLAR OLIB BORILMOQDA</b>\n\n"
    "Hozirda botimiz va Mini App’da texnik sozlash ishlari olib borilmoqda.\n\n"
    "⏳ Iltimos, birozdan so‘ng qayta urinib ko‘ring.\n\n"
    "🙏 Noqulaylik uchun uzr so‘raymiz!"
)

# ---- Yetkazib berish ----
DELIVERY_TEXT = "Yetkazish narxlari kelishilgan holatda."

# ---- Aloqa ma'lumotlari ----
CONTACT_TEXT = (
    "📞 <b>Telefon:</b>\n+998 55 500 10 06\n\n"
    "📍 <b>Manzil:</b>\nhttps://maps.app.goo.gl/YJf43hSMwrqSaZNm8?g_st=ic\n\n"
    "🕐 <b>Ish vaqti:</b>\nDushanba-Shanba, 08:00-17:30\n\n"
    "📱 <b>Qo‘shimcha aloqa:</b>\n@idealsetka_rasmiy"
)

# ---- To'lov ma'lumotlari ----
PAY_QR = "YAGONA QR-KOD"
PAY_CLICK = "CLICK"
PAY_PAYME = "PAYME"
PAY_CASH = "Naqd pul"

PAY_CODE_TO_NAME = {"QR": PAY_QR, "CLICK": PAY_CLICK, "PAYME": PAY_PAYME, "CASH": PAY_CASH}

CLICK_URL = "https://indoor.click.uz/pay?id=093152&t=0"
PAYME_URL = "https://transfer.paycom.uz/696e100aca1b11940e4e9bc6"
QR_PAYLOAD = (
    "00020101021140440012qr-online.uz01186r1G9gFpoakwOSEGAg0202015204591253038605502035703."
    "655802UZ5921IDEAL INTER FARM MCHJ600TANDIJON80320012qr-online.uz031299897473722163045B37"
)
