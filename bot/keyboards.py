# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import WEBAPP_URL, PAY_QR, PAY_CLICK, PAY_PAYME, PAY_CASH
from bot.utils import product_short_label, format_price


# ---------------------------------------------------------------------------
# Foydalanuvchi uchun
# ---------------------------------------------------------------------------
def main_menu_kb(categories, webapp_enabled: bool = True):
    rows = []
    if WEBAPP_URL and webapp_enabled:
        rows.append(
            [InlineKeyboardButton(text="🛒 Mini App / Buyurtma", web_app=WebAppInfo(url=WEBAPP_URL))]
        )
    for cat in categories:
        rows.append([InlineKeyboardButton(text=cat["name"], callback_data=f"cat:{cat['id']}")])
    rows.append([InlineKeyboardButton(text="📞 Aloqa", callback_data="contact")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_kb(products):
    rows = []
    for p in products:
        label = product_short_label(p)
        price_txt = format_price(p["price"])
        rows.append(
            [InlineKeyboardButton(text=f"{label} — {price_txt}", callback_data=f"prod:{p['id']}")]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Menyu", callback_data="back_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quantity_kb(product_id: int, unit: str):
    rows = [
        [
            InlineKeyboardButton(text="1", callback_data=f"qty:{product_id}:1"),
            InlineKeyboardButton(text="2", callback_data=f"qty:{product_id}:2"),
            InlineKeyboardButton(text="5", callback_data=f"qty:{product_id}:5"),
            InlineKeyboardButton(text="10", callback_data=f"qty:{product_id}:10"),
        ],
        [InlineKeyboardButton(text="✍️ Boshqa miqdor", callback_data=f"qty_custom:{product_id}")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def eco_confirm_kb(product_id: int):
    rows = [
        [InlineKeyboardButton(text="✅ Buyurtma berish (1 rulon)", callback_data=f"qty:{product_id}:1")],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_methods_kb():
    rows = [
        [InlineKeyboardButton(text=f"🟣 {PAY_QR}", callback_data="pay:QR")],
        [InlineKeyboardButton(text=f"🔵 {PAY_CLICK}", callback_data="pay:CLICK")],
        [InlineKeyboardButton(text=f"🟢 {PAY_PAYME}", callback_data="pay:PAYME")],
        [InlineKeyboardButton(text=f"💵 {PAY_CASH}", callback_data="pay:CASH")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def paid_done_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="💳 To‘lov qildim", callback_data="paid_done")]]
    )


def back_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Menyu", callback_data="back_menu")]]
    )


# ---------------------------------------------------------------------------
# Admin uchun
# ---------------------------------------------------------------------------
def admin_panel_kb(tech_on: bool, webapp_on: bool):
    tech_btn = (
        InlineKeyboardButton(text="🔴 Texnik rejim: O‘chirish", callback_data="admin:tech:off")
        if tech_on else
        InlineKeyboardButton(text="🟢 Texnik rejim: Yoqish", callback_data="admin:tech:on")
    )
    webapp_btn = (
        InlineKeyboardButton(text="🔴 Mini App: O‘chirish", callback_data="admin:webapp:off")
        if webapp_on else
        InlineKeyboardButton(text="🟢 Mini App: Yoqish", callback_data="admin:webapp:on")
    )
    rows = [
        [InlineKeyboardButton(text="📋 Mahsulotlar ro‘yxati", callback_data="admin:products")],
        [InlineKeyboardButton(text="➕ Mahsulot qo‘shish", callback_data="admin:addproduct")],
        [InlineKeyboardButton(text="🖼 Kategoriya rasmi yuklash", callback_data="admin:setimage")],
        [tech_btn],
        [webapp_btn],
        [InlineKeyboardButton(text="📦 So‘nggi buyurtmalar", callback_data="admin:orders")],
        [InlineKeyboardButton(text="🧾 So‘nggi cheklar", callback_data="admin:receipts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_category_pick_kb(categories, prefix: str):
    rows = [
        [InlineKeyboardButton(text=cat["name"], callback_data=f"{prefix}:{cat['id']}")]
        for cat in categories
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_unit_pick_kb():
    rows = [
        [
            InlineKeyboardButton(text="dona", callback_data="admin:unit:dona"),
            InlineKeyboardButton(text="rulon", callback_data="admin:unit:rulon"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Admin panel", callback_data="admin:back")]]
    )
