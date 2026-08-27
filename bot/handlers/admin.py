# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import is_admin
from database import models
from bot.keyboards import (
    admin_panel_kb, admin_category_pick_kb, admin_unit_pick_kb, admin_back_kb,
)
from bot.states import AdminStates
from bot.utils import product_full_description, format_price

router = Router()

_CHUNK_LIMIT = 3500


def _chunk_text(lines):
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) + 1 > _CHUNK_LIMIT:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current:
        chunks.append(current)
    return chunks


async def _guard_admin(user_id: int) -> bool:
    return is_admin(user_id)


# ---------------------------------------------------------------------------
# Admin panel bosh menyusi
# ---------------------------------------------------------------------------
@router.message(Command("admin"))
async def admin_panel(m: Message, state: FSMContext):
    if not await _guard_admin(m.from_user.id):
        return
    await state.clear()
    tech_on = await models.is_technical_mode()
    webapp_on = await models.is_webapp_enabled()
    await m.answer("⚙️ <b>Admin panel</b>", parse_mode="HTML", reply_markup=admin_panel_kb(tech_on, webapp_on))


@router.callback_query(F.data == "admin:back")
async def admin_back(c: CallbackQuery, state: FSMContext):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    await state.clear()
    tech_on = await models.is_technical_mode()
    webapp_on = await models.is_webapp_enabled()
    await c.message.answer("⚙️ <b>Admin panel</b>", parse_mode="HTML", reply_markup=admin_panel_kb(tech_on, webapp_on))
    await c.answer()


# ---------------------------------------------------------------------------
# Texnik rejim / Mini App yoqish-o'chirish
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("admin:tech:"))
async def toggle_tech(c: CallbackQuery):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    value = "true" if c.data.endswith(":on") else "false"
    await models.set_setting("technical_mode", value)
    tech_on = value == "true"
    webapp_on = await models.is_webapp_enabled()
    await c.message.edit_reply_markup(reply_markup=admin_panel_kb(tech_on, webapp_on))
    await c.answer("✅ Texnik rejim yangilandi.")


@router.callback_query(F.data.startswith("admin:webapp:"))
async def toggle_webapp(c: CallbackQuery):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    value = "true" if c.data.endswith(":on") else "false"
    await models.set_setting("webapp_enabled", value)
    webapp_on = value == "true"
    tech_on = await models.is_technical_mode()
    await c.message.edit_reply_markup(reply_markup=admin_panel_kb(tech_on, webapp_on))
    await c.answer("✅ Mini App holati yangilandi.")


# ---------------------------------------------------------------------------
# Mahsulotlar ro'yxati (admin panel tugmasi)
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "admin:products")
async def admin_products(c: CallbackQuery):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    await c.answer()
    await _send_products_list(c.message)


@router.message(Command("products"))
async def cmd_products(m: Message):
    if not is_admin(m.from_user.id):
        return
    await _send_products_list(m)


async def _send_products_list(m: Message):
    products = await models.get_all_active_products()
    if not products:
        await m.answer("Faol mahsulotlar topilmadi.", reply_markup=admin_back_kb())
        return
    lines, current_cat = [], None
    for p in products:
        if p["category_name"] != current_cat:
            current_cat = p["category_name"]
            lines.append(f"\n<b>{current_cat}</b>")
        desc = product_full_description(p)
        price_txt = format_price(p["price"])
        lines.append(f"#{p['id']} — {desc} — {price_txt} — {p['unit']}")
    chunks = _chunk_text(lines)
    for i, chunk in enumerate(chunks):
        kb = admin_back_kb() if i == len(chunks) - 1 else None
        await m.answer(chunk, parse_mode="HTML", reply_markup=kb)
    await m.answer(
        "✏️ O‘zgartirish uchun:\n"
        "/editprice &lt;id&gt; &lt;yangi_narx&gt;\n"
        "/editname &lt;id&gt; &lt;yangi_nom&gt;\n"
        "/delproduct &lt;id&gt;",
        parse_mode="HTML",
    )


@router.message(Command("editprice"))
async def edit_price(m: Message):
    if not is_admin(m.from_user.id):
        return
    args = (m.text or "").split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit() or not args[2].strip().isdigit():
        await m.answer("Foydalanish: /editprice <id> <yangi_narx>\nMisol: /editprice 3 350000")
        return
    product_id, new_price = int(args[1]), int(args[2].strip())
    ok = await models.update_product_price(product_id, new_price)
    await m.answer(
        f"✅ #{product_id} mahsulot narxi {format_price(new_price)} ga o‘zgartirildi."
        if ok else f"❗ #{product_id} ID bilan faol mahsulot topilmadi."
    )


@router.message(Command("editname"))
async def edit_name(m: Message):
    if not is_admin(m.from_user.id):
        return
    args = (m.text or "").split(maxsplit=2)
    if len(args) < 3 or not args[1].isdigit():
        await m.answer("Foydalanish: /editname <id> <yangi_nom>\nMisol: /editname 3 RANGLI")
        return
    product_id, new_name = int(args[1]), args[2].strip()
    ok = await models.update_product_name(product_id, new_name)
    await m.answer(
        f"✅ #{product_id} mahsulot nomi \"{new_name}\" ga o‘zgartirildi."
        if ok else f"❗ #{product_id} ID bilan faol mahsulot topilmadi."
    )


@router.message(Command("delproduct"))
async def delete_product(m: Message):
    if not is_admin(m.from_user.id):
        return
    args = (m.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await m.answer("Foydalanish: /delproduct <id>\nMisol: /delproduct 3")
        return
    product_id = int(args[1].strip())
    ok = await models.deactivate_product(product_id)
    await m.answer(
        f"✅ #{product_id} mahsulot faol ro‘yxatdan olib tashlandi (active=0)."
        if ok else f"❗ #{product_id} ID bilan faol mahsulot topilmadi."
    )


# ---------------------------------------------------------------------------
# Mahsulot qo'shish (FSM)
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "admin:addproduct")
async def add_product_start(c: CallbackQuery, state: FSMContext):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    categories = await models.get_categories()
    await state.set_state(AdminStates.add_product_category)
    await c.message.answer("Qaysi kategoriyaga mahsulot qo‘shmoqchisiz?", reply_markup=admin_category_pick_kb(categories, "admin:pcat"))
    await c.answer()


@router.callback_query(AdminStates.add_product_category, F.data.startswith("admin:pcat:"))
async def add_product_category(c: CallbackQuery, state: FSMContext):
    category_id = int(c.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.add_product_size)
    await c.message.answer(
        "Mahsulot razmeri/tavsifini kiriting.\n"
        "Masalan: <code>1.6/50×50/2×10m</code> yoki <code>RANGLI 0.8/20*10/120m</code>",
        parse_mode="HTML",
    )
    await c.answer()


@router.message(AdminStates.add_product_size)
async def add_product_size(m: Message, state: FSMContext):
    if not (m.text and m.text.strip()):
        await m.answer("Iltimos, razmer/tavsifni matn ko‘rinishida kiriting.")
        return
    await state.update_data(size=m.text.strip())
    await state.set_state(AdminStates.add_product_price)
    await m.answer("Narxini kiriting (faqat son, so‘m). Masalan: 250000")


@router.message(AdminStates.add_product_price)
async def add_product_price(m: Message, state: FSMContext):
    text = (m.text or "").strip()
    if not text.isdigit():
        await m.answer("❗ Iltimos, narxni faqat butun son bilan kiriting. Masalan: 250000")
        return
    await state.update_data(price=int(text))
    await state.set_state(AdminStates.add_product_unit)
    await m.answer("Sotuv birligini tanlang:", reply_markup=admin_unit_pick_kb())


@router.callback_query(AdminStates.add_product_unit, F.data.startswith("admin:unit:"))
async def add_product_unit(c: CallbackQuery, state: FSMContext):
    unit = c.data.split(":")[2]
    data = await state.get_data()
    product_id = await models.add_product(
        category_id=data["category_id"], size=data["size"], price=data["price"], unit=unit,
    )
    await state.clear()
    await c.message.answer(f"✅ Mahsulot qo‘shildi (#{product_id}).", reply_markup=admin_back_kb())
    await c.answer()


# ---------------------------------------------------------------------------
# Kategoriya rasmi yuklash (FSM)
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "admin:setimage")
async def set_image_start(c: CallbackQuery, state: FSMContext):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    categories = await models.get_categories()
    await state.set_state(AdminStates.set_image_category)
    await c.message.answer("Qaysi kategoriyaga rasm yuklamoqchisiz?", reply_markup=admin_category_pick_kb(categories, "admin:icat"))
    await c.answer()


@router.callback_query(AdminStates.set_image_category, F.data.startswith("admin:icat:"))
async def set_image_category(c: CallbackQuery, state: FSMContext):
    category_id = int(c.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminStates.set_image_waiting_photo)
    await c.message.answer("📸 Ushbu kategoriya uchun rasmni yuboring.")
    await c.answer()


@router.message(AdminStates.set_image_waiting_photo, F.photo)
async def set_image_receive(m: Message, state: FSMContext):
    data = await state.get_data()
    file_id = m.photo[-1].file_id
    ok = await models.set_category_image(data["category_id"], file_id)
    await state.clear()
    await m.answer(
        "✅ Kategoriya rasmi yangilandi." if ok else "❗ Kategoriya topilmadi.",
        reply_markup=admin_back_kb(),
    )


@router.message(AdminStates.set_image_waiting_photo)
async def set_image_invalid(m: Message):
    await m.answer("❗ Iltimos, rasm (screenshot/fotosurat) ko‘rinishida yuboring.")


# ---------------------------------------------------------------------------
# Buyurtmalar / cheklar
# ---------------------------------------------------------------------------
@router.callback_query(F.data == "admin:orders")
async def admin_orders(c: CallbackQuery):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    orders = await models.get_recent_orders(10)
    if not orders:
        await c.message.answer("Buyurtmalar topilmadi.", reply_markup=admin_back_kb())
        return await c.answer()
    lines = ["📦 <b>So‘nggi buyurtmalar</b>\n"]
    for o in orders:
        lines.append(
            f"#{o['order_code']} — {o['full_name'] or '-'} — {format_price(o['total'])} — "
            f"{o['payment_method'] or '-'} — {o['status']}"
        )
    await c.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=admin_back_kb())
    await c.answer()


@router.callback_query(F.data == "admin:receipts")
async def admin_receipts(c: CallbackQuery):
    if not await _guard_admin(c.from_user.id):
        return await c.answer()
    receipts = await models.get_recent_receipts(10)
    if not receipts:
        await c.message.answer("Cheklar topilmadi.", reply_markup=admin_back_kb())
        return await c.answer()
    await c.answer()
    for r in receipts:
        await c.message.answer_photo(r["file_id"], caption=f"🧾 Buyurtma: #{r['order_code']}")
    await c.message.answer("⬅️", reply_markup=admin_back_kb())
