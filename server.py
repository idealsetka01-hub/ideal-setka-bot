# -*- coding: utf-8 -*-
"""
FastAPI backend: Telegram Mini App uchun statik fayllarni va REST API'ni xizmat qiladi.
Mini App orqali berilgan buyurtmalar shu yerdan bot.orders.finalize_order() orqali
bevosita Telegram bot backendiga (bir xil bazaga) yoziladi va adminlarga yuboriladi.
"""
import io
import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conint, constr

from config import TECH_TEXT, PAY_CODE_TO_NAME
from database import models
from bot import bot_instance
from bot.orders import finalize_order
from bot.utils import product_full_description, format_price

app = FastAPI(title="IDEAL SETKA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# "static" papkasi bo'sh bo'lgani uchun ba'zan Git orqali (yoki qo'lda GitHub
# veb-interfeysi orqali) yuklanmay qolishi mumkin. StaticFiles papka jismonan
# mavjud bo'lishini talab qiladi, shu sababli ishga tushishda o'zimiz yaratamiz —
# bu bilan GitHub'da bo'sh papka bilan ovora bo'lish shart emas.
os.makedirs("static", exist_ok=True)
os.makedirs("webapp", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/app", StaticFiles(directory="webapp", html=True), name="webapp")


# ---------------------------------------------------------------------------
# Health check (Render bu manzilga muntazam so'rov yuborib xizmat tiriqligini tekshiradi)
# ---------------------------------------------------------------------------
@app.get("/")
async def health_root():
    return {"status": "ok", "service": "ideal-setka-bot"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Sozlamalar
# ---------------------------------------------------------------------------
@app.get("/api/settings")
async def api_settings():
    return {
        "technical_mode": await models.is_technical_mode(),
        "webapp_enabled": await models.is_webapp_enabled(),
    }


async def _guard() -> None:
    if await models.is_technical_mode():
        raise HTTPException(status_code=503, detail=TECH_TEXT)
    if not await models.is_webapp_enabled():
        raise HTTPException(status_code=503, detail="Mini App vaqtincha o‘chirilgan.")


# ---------------------------------------------------------------------------
# Kategoriyalar / mahsulotlar
# ---------------------------------------------------------------------------
@app.get("/api/categories")
async def api_categories():
    await _guard()
    categories = await models.get_categories()
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "image_url": f"/api/image/{c['image_file_id']}" if c["image_file_id"] else None,
        }
        for c in categories
    ]


@app.get("/api/products/{category_id}")
async def api_products(category_id: int):
    await _guard()
    products = await models.get_active_products(category_id)
    return [
        {
            "id": p["id"],
            "desc": product_full_description(p),
            "size": p["size"],
            "price": p["price"],
            "price_text": format_price(p["price"]),
            "unit": p["unit"],
            "is_eco_roll": bool(p["is_eco_roll"]),
        }
        for p in products
    ]


@app.get("/api/image/{file_id}")
async def api_image(file_id: str):
    """Telegram file_id orqali saqlangan kategoriya rasmini proxy qilib beradi."""
    try:
        bot = bot_instance.get_bot()
        tg_file = await bot.get_file(file_id)
        buf = io.BytesIO()
        await bot.download_file(tg_file.file_path, destination=buf)
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/jpeg")
    except Exception:
        raise HTTPException(status_code=404, detail="Rasm topilmadi")


# ---------------------------------------------------------------------------
# Buyurtma
# ---------------------------------------------------------------------------
class OrderItemIn(BaseModel):
    product_id: int
    qty: conint(gt=0)


class OrderIn(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: constr(min_length=1)
    phone: constr(min_length=3)
    address: constr(min_length=1)
    payment_method: str  # "QR" | "CLICK" | "PAYME"
    items: list[OrderItemIn]


@app.post("/api/order")
async def api_create_order(payload: OrderIn):
    await _guard()

    if not payload.items:
        raise HTTPException(status_code=400, detail="Savat bo‘sh.")

    method = PAY_CODE_TO_NAME.get(payload.payment_method)
    if not method:
        raise HTTPException(status_code=400, detail="Noma'lum to‘lov usuli.")

    items = []
    for it in payload.items:
        p = await models.get_product(it.product_id)
        if not p or not p["active"]:
            raise HTTPException(status_code=400, detail=f"#{it.product_id} mahsulot topilmadi.")
        items.append({
            "product_id": p["id"],
            "product_desc": product_full_description(p),
            "size": p["size"],
            "qty": it.qty,
            "unit": p["unit"],
            "price": p["price"],
        })

    result = await finalize_order(
        telegram_id=payload.telegram_id,
        username=payload.username,
        full_name=payload.full_name,
        phone=payload.phone,
        address=payload.address,
        payment_method=method,
        items=items,
        source="webapp",
    )

    # Barcha to'lov usullari online bo'lgani uchun chek har doim talab qilinadi.
    try:
        bot = bot_instance.get_bot()
        await bot.send_message(
            payload.telegram_id,
            f"🧾 Buyurtmangiz (#{result['order_code']}) qabul qilindi.\n\n"
            f"Iltimos, to‘lov chekini shu chatga rasm shaklida yuboring.",
        )
    except Exception:
        pass

    return {
        "order_code": result["order_code"],
        "total": result["total"],
        "needs_receipt": True,
    }
