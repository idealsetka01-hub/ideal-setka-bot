# -*- coding: utf-8 -*-
"""SQLite ulanish yordamchilari, sxema va boshlang'ich (seed) ma'lumotlar."""
import os
import aiosqlite

from config import DB_PATH
from database.products_data import CATEGORY_ORDER, PRODUCTS

# DB_PATH pastki papkada bo'lishi mumkin (masalan Render doimiy diskida "data/ideal_setka.db").
# Papka mavjud bo'lmasa, sqlite fayl yarata olmaydi — shu sababli oldindan yaratib qo'yamiz.
_db_dir = os.path.dirname(DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    full_name TEXT,
    first_seen TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    sort_order INTEGER NOT NULL,
    image_file_id TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    name TEXT,
    wire TEXT,
    cell TEXT,
    size TEXT,
    spec TEXT,
    price INTEGER,
    unit TEXT NOT NULL,
    is_eco_roll INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT UNIQUE,
    telegram_id INTEGER,
    username TEXT,
    full_name TEXT,
    phone TEXT,
    address TEXT,
    payment_method TEXT,
    total INTEGER,
    status TEXT DEFAULT 'yangi',
    source TEXT DEFAULT 'bot',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER,
    product_desc TEXT,
    size TEXT,
    qty INTEGER,
    unit TEXT,
    price INTEGER,
    subtotal INTEGER
);

CREATE TABLE IF NOT EXISTS receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    file_id TEXT NOT NULL,
    uploaded_at TEXT
);
"""

DEFAULT_SETTINGS = {
    "technical_mode": "false",
    "webapp_enabled": "true",
}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
        await _seed_settings(db)
        await _seed_products_if_empty(db)


async def _seed_settings(db: aiosqlite.Connection):
    for key, value in DEFAULT_SETTINGS.items():
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
    await db.commit()


async def _seed_products_if_empty(db: aiosqlite.Connection):
    cur = await db.execute("SELECT COUNT(*) FROM categories")
    (count,) = await cur.fetchone()
    if count > 0:
        # Baza allaqachon to'ldirilgan bo'lsa qayta urug'lantirmaymiz —
        # shu sababli qayta ishga tushirishda mahsulotlar takrorlanmaydi.
        return

    for sort_order, cat_name in enumerate(CATEGORY_ORDER):
        cur = await db.execute(
            "INSERT INTO categories (name, sort_order) VALUES (?, ?)", (cat_name, sort_order)
        )
        category_id = cur.lastrowid
        for p in PRODUCTS.get(cat_name, []):
            await db.execute(
                """INSERT INTO products
                   (category_id, name, wire, cell, size, spec, price, unit, is_eco_roll, active)
                   VALUES (?,?,?,?,?,?,?,?,?,1)""",
                (
                    category_id,
                    p.get("name"),
                    p.get("wire"),
                    p.get("cell"),
                    p.get("size"),
                    p.get("spec"),
                    p.get("price"),
                    p.get("unit", "dona"),
                    1 if p.get("is_eco_roll") else 0,
                ),
            )
    await db.commit()


def get_connection():
    """Har bir chaqiruvda yangi aiosqlite ulanishi (async context manager sifatida ishlatiladi)."""
    return aiosqlite.connect(DB_PATH)
