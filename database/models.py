# -*- coding: utf-8 -*-
"""Barcha jadvallar uchun async CRUD funksiyalari (aiosqlite orqali)."""
import datetime

from database.db import get_connection


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
async def upsert_user(telegram_id: int, username: str, full_name: str):
    async with get_connection() as db:
        cur = await db.execute("SELECT id FROM users WHERE telegram_id=?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username=?, full_name=? WHERE telegram_id=?",
                (username, full_name, telegram_id),
            )
        else:
            await db.execute(
                "INSERT INTO users (telegram_id, username, full_name, first_seen) VALUES (?,?,?,?)",
                (telegram_id, username, full_name, datetime.datetime.now().isoformat(timespec="seconds")),
            )
        await db.commit()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
async def get_setting(key: str, default: str = None):
    async with get_connection() as db:
        cur = await db.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = await cur.fetchone()
        return row[0] if row else default


async def set_setting(key: str, value: str):
    async with get_connection() as db:
        await db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        await db.commit()


async def is_technical_mode() -> bool:
    return (await get_setting("technical_mode", "false")) == "true"


async def is_webapp_enabled() -> bool:
    return (await get_setting("webapp_enabled", "true")) == "true"


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
async def get_categories():
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories ORDER BY sort_order")
        return await cur.fetchall()


async def get_category(category_id: int):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM categories WHERE id=?", (category_id,))
        return await cur.fetchone()


async def set_category_image(category_id: int, file_id: str) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "UPDATE categories SET image_file_id=? WHERE id=?", (file_id, category_id)
        )
        await db.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
async def get_active_products(category_id: int):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM products WHERE category_id=? AND active=1 ORDER BY id", (category_id,)
        )
        return await cur.fetchall()


async def get_product(product_id: int):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE id=?", (product_id,))
        return await cur.fetchone()


async def get_all_active_products():
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT products.*, categories.name AS category_name
               FROM products JOIN categories ON products.category_id = categories.id
               WHERE products.active=1
               ORDER BY categories.sort_order, products.id"""
        )
        return await cur.fetchall()


async def add_product(category_id: int, size: str, price: int, unit: str,
                       name: str = None, wire: str = None, cell: str = None, spec: str = None,
                       is_eco_roll: bool = False) -> int:
    async with get_connection() as db:
        cur = await db.execute(
            """INSERT INTO products (category_id, name, wire, cell, size, spec, price, unit, is_eco_roll, active)
               VALUES (?,?,?,?,?,?,?,?,?,1)""",
            (category_id, name, wire, cell, size, spec, price, unit, 1 if is_eco_roll else 0),
        )
        await db.commit()
        return cur.lastrowid


async def update_product_price(product_id: int, price: int) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "UPDATE products SET price=? WHERE id=? AND active=1", (price, product_id)
        )
        await db.commit()
        return cur.rowcount > 0


async def update_product_name(product_id: int, name: str) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "UPDATE products SET name=? WHERE id=? AND active=1", (name, product_id)
        )
        await db.commit()
        return cur.rowcount > 0


async def deactivate_product(product_id: int) -> bool:
    async with get_connection() as db:
        cur = await db.execute(
            "UPDATE products SET active=0 WHERE id=? AND active=1", (product_id,)
        )
        await db.commit()
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Orders / order items / receipts
# ---------------------------------------------------------------------------
async def create_order(telegram_id: int, username: str, full_name: str, phone: str, address: str,
                        payment_method: str, items: list, status: str, source: str) -> dict:
    """
    items: [{"product_id":, "product_desc":, "size":, "qty":, "unit":, "price":}, ...]
    Qaytaradi: {"order_id":, "order_code":, "total":}
    """
    total = sum((it["price"] or 0) * it["qty"] for it in items)
    created_at = datetime.datetime.now().isoformat(timespec="seconds")

    async with get_connection() as db:
        cur = await db.execute(
            """INSERT INTO orders (telegram_id, username, full_name, phone, address,
               payment_method, total, status, source, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (telegram_id, username, full_name, phone, address, payment_method, total, status, source, created_at),
        )
        order_id = cur.lastrowid
        order_code = f"IS-{order_id:06d}"
        await db.execute("UPDATE orders SET order_code=? WHERE id=?", (order_code, order_id))

        for it in items:
            subtotal = (it["price"] or 0) * it["qty"]
            await db.execute(
                """INSERT INTO order_items (order_id, product_id, product_desc, size, qty, unit, price, subtotal)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (order_id, it.get("product_id"), it.get("product_desc"), it.get("size"),
                 it.get("qty"), it.get("unit"), it.get("price"), subtotal),
            )
        await db.commit()

    return {"order_id": order_id, "order_code": order_code, "total": total}


async def get_order(order_id: int):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
        return await cur.fetchone()


async def get_order_items(order_id: int):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,))
        return await cur.fetchall()


async def find_pending_order_for_user(telegram_id: int):
    """Foydalanuvchining online to'lov chekini kutayotgan so'nggi buyurtmasi (Mini App yoki botdan)."""
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM orders WHERE telegram_id=? AND status='kutilmoqda_tolov' ORDER BY id DESC LIMIT 1",
            (telegram_id,),
        )
        return await cur.fetchone()


async def attach_receipt(order_id: int, file_id: str):
    async with get_connection() as db:
        await db.execute(
            "INSERT INTO receipts (order_id, file_id, uploaded_at) VALUES (?,?,?)",
            (order_id, file_id, datetime.datetime.now().isoformat(timespec="seconds")),
        )
        await db.execute("UPDATE orders SET status='chek_yuborildi' WHERE id=?", (order_id,))
        await db.commit()


async def update_order_status(order_id: int, status: str):
    async with get_connection() as db:
        await db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        await db.commit()


async def get_recent_orders(limit: int = 10):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
        return await cur.fetchall()


async def get_recent_receipts(limit: int = 10):
    import aiosqlite
    async with get_connection() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT receipts.*, orders.order_code AS order_code
               FROM receipts JOIN orders ON receipts.order_id = orders.id
               ORDER BY receipts.id DESC LIMIT ?""",
            (limit,),
        )
        return await cur.fetchall()
