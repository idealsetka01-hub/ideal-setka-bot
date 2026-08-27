# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import TECH_TEXT
from database import models
from bot.keyboards import products_kb

router = Router()


@router.callback_query(F.data.startswith("cat:"))
async def show_category(c: CallbackQuery, state):
    if await models.is_technical_mode():
        await c.message.answer(TECH_TEXT, parse_mode="HTML")
        return await c.answer()

    await state.clear()
    category_id = int(c.data.split(":")[1])
    category = await models.get_category(category_id)
    if not category:
        await c.answer("Kategoriya topilmadi.", show_alert=True)
        return

    products = await models.get_active_products(category_id)
    if not products:
        await c.message.answer(f"<b>{category['name']}</b>\n\nHozircha mahsulot mavjud emas.", parse_mode="HTML")
        return await c.answer()

    caption = f"<b>{category['name']}</b>\n\nKerakli mahsulotni tanlang:"
    kb = products_kb(products)

    if category["image_file_id"]:
        await c.message.answer_photo(category["image_file_id"], caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await c.message.answer(caption, parse_mode="HTML", reply_markup=kb)
    await c.answer()
