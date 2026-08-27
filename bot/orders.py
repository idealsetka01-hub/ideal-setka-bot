# -*- coding: utf-8 -*-
"""
Buyurtmani yakunlash va adminlarga xabar yuborish — bot va Mini App (FastAPI)
ikkalasi ham shu funksiyalardan foydalanadi, shu bilan bitta manba (single source
of truth) saqlanadi.
"""
from config import ADMIN_IDS, DELIVERY_TEXT, PAY_CASH
from database import models
from bot.utils import format_price
from bot import bot_instance


def _build_order_text(order_code: str, full_name: str, phone: str, address: str,
                       items, total, payment_method: str) -> str:
    lines = [
        "🛒 <b>YANGI BUYURTMA</b>\n",
        f"📦 Buyurtma: #{order_code}",
        f"👤 Mijoz: {full_name}",
        f"📞 Telefon: {phone}",
        f"📍 Manzil: {address}\n",
        "Mahsulotlar:",
    ]
    for it in items:
        price_txt = format_price(it.get("price"))
        lines.append(f"• {it.get('product_desc')} ({it.get('size') or '-'}) — {it.get('qty')} {it.get('unit')} × {price_txt}")

    pay_icon = "💵" if payment_method == PAY_CASH else "💳"
    lines.append(f"\n💰 Jami: {format_price(total)}")
    lines.append(f"{pay_icon} To‘lov: {payment_method}")
    lines.append(f"\n🚚 Yetkazib berish: {DELIVERY_TEXT}")
    return "\n".join(lines)


async def notify_admins_new_order(order_code: str, full_name: str, phone: str, address: str,
                                   items, total, payment_method: str, receipt_file_id: str = None):
    bot = bot_instance.get_bot()
    text = _build_order_text(order_code, full_name, phone, address, items, total, payment_method)
    for admin_id in ADMIN_IDS:
        try:
            if receipt_file_id:
                await bot.send_photo(admin_id, receipt_file_id, caption=text, parse_mode="HTML")
            else:
                await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception:
            # Admin botni bloklagan yoki hali /start bosmagan bo'lishi mumkin.
            continue


async def finalize_order(telegram_id: int, username: str, full_name: str, phone: str, address: str,
                          payment_method: str, items: list, source: str, receipt_file_id: str = None) -> dict:
    """
    Buyurtmani bazaga yozadi. Naqd pul bo'lsa yoki chek allaqachon bor bo'lsa —
    darhol adminlarga yuboradi. Online to'lov (chek hali yo'q) bo'lsa — holatni
    'kutilmoqda_tolov' qilib qo'yadi va chek kelgach xabar yuboriladi.
    """
    if payment_method == PAY_CASH or receipt_file_id:
        status = "chek_yuborildi" if receipt_file_id and payment_method != PAY_CASH else "yangi"
    else:
        status = "kutilmoqda_tolov"

    result = await models.create_order(
        telegram_id=telegram_id, username=username, full_name=full_name, phone=phone,
        address=address, payment_method=payment_method, items=items, status=status, source=source,
    )

    if receipt_file_id:
        await models.attach_receipt(result["order_id"], receipt_file_id)

    if status in ("yangi", "chek_yuborildi"):
        await notify_admins_new_order(
            result["order_code"], full_name, phone, address, items, result["total"],
            payment_method, receipt_file_id=receipt_file_id,
        )

    return result


async def attach_receipt_and_notify(order_id: int, file_id: str):
    await models.attach_receipt(order_id, file_id)
    order = await models.get_order(order_id)
    items_rows = await models.get_order_items(order_id)
    items = [
        {
            "product_desc": r["product_desc"], "size": r["size"], "qty": r["qty"],
            "unit": r["unit"], "price": r["price"],
        }
        for r in items_rows
    ]
    await notify_admins_new_order(
        order["order_code"], order["full_name"], order["phone"], order["address"],
        items, order["total"], order["payment_method"], receipt_file_id=file_id,
    )
