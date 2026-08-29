# -*- coding: utf-8 -*-
import io

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config import (
    TECH_TEXT, DELIVERY_TEXT,
    PAY_QR, PAY_CLICK, PAY_PAYME, PAY_CODE_TO_NAME,
    CLICK_URL, PAYME_URL, QR_PAYLOAD,
)
from database import models
from bot.keyboards import (
    quantity_kb, payment_methods_kb, paid_done_kb, back_menu_kb,
)
from bot.states import OrderStates
from bot.utils import product_full_description, format_price, only_int_or_none
from bot.orders import finalize_order, attach_receipt_and_notify

router = Router()


async def _tech_blocked(c: CallbackQuery) -> bool:
    if await models.is_technical_mode():
        await c.message.answer(TECH_TEXT, parse_mode="HTML")
        await c.answer()
        return True
    return False


# ---------------------------------------------------------------------------
# 1) Mahsulot tanlash
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("prod:"))
async def show_product(c: CallbackQuery, state: FSMContext):
    if await _tech_blocked(c):
        return

    product_id = int(c.data.split(":")[1])
    p = await models.get_product(product_id)
    if not p or not p["active"]:
        await c.answer("Bu mahsulot mavjud emas.", show_alert=True)
        return

    desc = product_full_description(p)
    price_txt = format_price(p["price"])
    await state.update_data(
        product_id=p["id"], product_desc=desc, price=p["price"], unit=p["unit"], size=p["size"],
    )

    # ECO ZABOR uchun ham endi miqdor so'raladi (avval avtomatik 1 rulon edi) —
    # faqat "har rulon = 10 metr" degan izoh qo'shimcha ko'rsatiladi.
    eco_note = "\n\n📏 Har 1 rulon = standart 10 metr" if p["is_eco_roll"] else ""
    text = (
        f"<b>{desc}</b>\nNarxi: {price_txt} — {p['unit']}\n\n"
        f"🚚 Yetkazib berish: {DELIVERY_TEXT}"
        f"{eco_note}\n\n"
        f"Nechta {p['unit']} kerak?"
    )
    await c.message.answer(text, parse_mode="HTML", reply_markup=quantity_kb(p["id"], p["unit"]))
    await c.answer()


# ---------------------------------------------------------------------------
# 2) Miqdorni tanlash
# ---------------------------------------------------------------------------
async def _confirm_qty_and_ask_name(target, state: FSMContext, qty: int):
    """Miqdor tanlangach summani hisoblab ko'rsatadi, so'ng ism so'raydi."""
    data = await state.get_data()
    price = data.get("price")
    unit = data.get("unit", "dona")

    if price is not None:
        total = price * qty
        calc_text = f"🧮 {qty} {unit} × {format_price(price)} = {format_price(total)}"
    else:
        calc_text = "🧮 Bu mahsulot narxi hali admin tomonidan belgilanmagan — operator siz bilan bog‘lanadi."

    await state.set_state(OrderStates.entering_name)
    await target.answer(f"{calc_text}\n\n👤 Ismingizni kiriting:", reply_markup=back_menu_kb())


@router.callback_query(F.data.startswith("qty:"))
async def choose_quantity(c: CallbackQuery, state: FSMContext):
    if await _tech_blocked(c):
        return

    _, product_id, qty = c.data.split(":")
    product_id, qty = int(product_id), int(qty)

    data = await state.get_data()
    if data.get("product_id") != product_id:
        p = await models.get_product(product_id)
        if not p:
            await c.answer("Mahsulot topilmadi.", show_alert=True)
            return
        await state.update_data(
            product_id=p["id"], product_desc=product_full_description(p),
            price=p["price"], unit=p["unit"], size=p["size"],
        )

    await state.update_data(qty=qty)
    await _confirm_qty_and_ask_name(c.message, state, qty)
    await c.answer()


@router.callback_query(F.data.startswith("qty_custom:"))
async def ask_custom_quantity(c: CallbackQuery, state: FSMContext):
    if await _tech_blocked(c):
        return

    product_id = int(c.data.split(":")[1])
    data = await state.get_data()
    if data.get("product_id") != product_id:
        p = await models.get_product(product_id)
        if not p:
            await c.answer("Mahsulot topilmadi.", show_alert=True)
            return
        await state.update_data(
            product_id=p["id"], product_desc=product_full_description(p),
            price=p["price"], unit=p["unit"], size=p["size"],
        )
    await state.set_state(OrderStates.choosing_quantity)
    await c.message.answer("Miqdorni butun son bilan kiriting (masalan: 3):")
    await c.answer()


@router.message(OrderStates.choosing_quantity)
async def receive_custom_quantity(m: Message, state: FSMContext):
    qty = only_int_or_none(m.text or "")
    if qty is None:
        await m.answer("❗ Faqat butun son kiriting (kasr son qabul qilinmaydi). Masalan: 1, 2, 5, 10")
        return
    await state.update_data(qty=qty)
    await _confirm_qty_and_ask_name(m, state, qty)


# ---------------------------------------------------------------------------
# 3) Mijoz ma'lumotlari
# ---------------------------------------------------------------------------
@router.message(OrderStates.entering_name)
async def receive_name(m: Message, state: FSMContext):
    if not (m.text and m.text.strip()):
        await m.answer("Iltimos, ismingizni matn ko‘rinishida kiriting.")
        return
    await state.update_data(full_name=m.text.strip())
    await state.set_state(OrderStates.entering_phone)
    await m.answer("📞 Telefon raqamingizni kiriting (masalan: +998901234567):")


@router.message(OrderStates.entering_phone)
async def receive_phone(m: Message, state: FSMContext):
    if not (m.text and m.text.strip()):
        await m.answer("Iltimos, telefon raqamingizni matn ko‘rinishida kiriting.")
        return
    await state.update_data(phone=m.text.strip())
    await state.set_state(OrderStates.entering_address)
    await m.answer("📍 Yetkazib berish manzilingizni kiriting:")


@router.message(OrderStates.entering_address)
async def receive_address(m: Message, state: FSMContext):
    if not (m.text and m.text.strip()):
        await m.answer("Iltimos, manzilingizni matn ko‘rinishida kiriting.")
        return
    await state.update_data(address=m.text.strip())
    await state.set_state(OrderStates.choosing_payment)
    await m.answer("💳 To‘lov usulini tanlang:", reply_markup=payment_methods_kb())


# ---------------------------------------------------------------------------
# 4) To'lov usuli
# ---------------------------------------------------------------------------
@router.callback_query(OrderStates.choosing_payment, F.data.startswith("pay:"))
async def choose_payment(c: CallbackQuery, state: FSMContext):
    code = c.data.split(":")[1]
    method = PAY_CODE_TO_NAME.get(code)
    if not method:
        await c.answer("Noma'lum to‘lov usuli.", show_alert=True)
        return

    await state.update_data(payment_method=method)

    if method == PAY_CLICK:
        text = (
            f"🔵 <b>{PAY_CLICK}</b> orqali to‘lov\n\nTo‘lov havolasi:\n{CLICK_URL}\n\n"
            f"To‘lovni amalga oshirgach, quyidagi tugmani bosing va chekni rasm shaklida yuboring."
        )
        await c.message.answer(text, parse_mode="HTML", reply_markup=paid_done_kb(), disable_web_page_preview=True)
    elif method == PAY_PAYME:
        text = (
            f"🟢 <b>{PAY_PAYME}</b> orqali to‘lov\n\nTo‘lov havolasi:\n{PAYME_URL}\n\n"
            f"To‘lovni amalga oshirgach, quyidagi tugmani bosing va chekni rasm shaklida yuboring."
        )
        await c.message.answer(text, parse_mode="HTML", reply_markup=paid_done_kb(), disable_web_page_preview=True)
    elif method == PAY_QR:
        try:
            import qrcode
            img = qrcode.make(QR_PAYLOAD)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            photo = BufferedInputFile(buf.read(), filename="yagona_qr.png")
            await c.message.answer_photo(
                photo,
                caption=(
                    f"🟣 <b>{PAY_QR}</b>\n\nQR kodni bank ilovasi orqali skanerlab to‘lovni amalga oshiring.\n"
                    f"To‘lovni amalga oshirgach, quyidagi tugmani bosing va chekni rasm shaklida yuboring."
                ),
                parse_mode="HTML",
                reply_markup=paid_done_kb(),
            )
        except Exception:
            await c.message.answer(
                f"🟣 <b>{PAY_QR}</b>\n\nTo‘lov kodi:\n<code>{QR_PAYLOAD}</code>\n\n"
                f"To‘lovni amalga oshirgach, quyidagi tugmani bosing va chekni rasm shaklida yuboring.",
                parse_mode="HTML",
                reply_markup=paid_done_kb(),
            )

    await state.set_state(OrderStates.waiting_receipt)
    await c.answer()


@router.callback_query(OrderStates.waiting_receipt, F.data == "paid_done")
async def paid_done(c: CallbackQuery, state: FSMContext):
    await c.message.answer("📸 Iltimos, to‘lov chekini rasm (screenshot) ko‘rinishida yuboring.")
    await c.answer()


@router.message(OrderStates.waiting_receipt, F.photo)
async def receive_receipt(m: Message, state: FSMContext):
    receipt_file_id = m.photo[-1].file_id
    await _finalize(m, state, receipt_file_id=receipt_file_id)


@router.message(OrderStates.waiting_receipt)
async def receive_receipt_invalid(m: Message):
    await m.answer("❗ Iltimos, to‘lov chekini aynan rasm (screenshot) ko‘rinishida yuboring.")


# ---------------------------------------------------------------------------
# Mini App orqali berilgan buyurtma uchun kutilayotgan chek (holat mavjud bo'lmaganda)
# ---------------------------------------------------------------------------
@router.message(F.photo)
async def receive_receipt_no_state(m: Message, state: FSMContext):
    current = await state.get_state()
    if current is not None:
        return  # boshqa handler allaqachon ishladi (yoki hali FSM tugamagan)

    pending = await models.find_pending_order_for_user(m.from_user.id)
    if not pending:
        return  # kutilayotgan buyurtma yo'q — e'tiborsiz qoldiramiz

    await attach_receipt_and_notify(pending["id"], m.photo[-1].file_id)
    await m.answer(
        f"✅ Chekingiz qabul qilindi. Buyurtmangiz tekshirilmoqda.\n\n🆔 Buyurtma: #{pending['order_code']}"
    )


# ---------------------------------------------------------------------------
# Yakunlash
# ---------------------------------------------------------------------------
async def _finalize(m: Message, state: FSMContext, receipt_file_id: str = None):
    data = await state.get_data()
    qty = data.get("qty", 1)
    price = data.get("price")

    items = [{
        "product_id": data.get("product_id"),
        "product_desc": data.get("product_desc"),
        "size": data.get("size"),
        "qty": qty,
        "unit": data.get("unit"),
        "price": price,
    }]

    result = await finalize_order(
        telegram_id=m.chat.id,
        username=getattr(m.chat, "username", None),
        full_name=data.get("full_name"),
        phone=data.get("phone"),
        address=data.get("address"),
        payment_method=data.get("payment_method"),
        items=items,
        source="bot",
        receipt_file_id=receipt_file_id,
    )

    total_txt = format_price(result["total"])
    if receipt_file_id:
        await m.answer(
            f"✅ Chekingiz qabul qilindi. Buyurtmangiz tekshirilmoqda.\n\n"
            f"🆔 Buyurtma raqami: #{result['order_code']}\n🧾 Jami summa: {total_txt}"
        )
    else:
        await m.answer(
            f"✅ Buyurtmangiz qabul qilindi!\n\n"
            f"🆔 Buyurtma raqami: #{result['order_code']}\n🧾 Jami summa: {total_txt}\n\n"
            f"Tez orada operatorlarimiz siz bilan bog‘lanishadi. Rahmat! 🙏"
        )
    await state.clear()
