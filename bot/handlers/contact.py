# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import TECH_TEXT, CONTACT_TEXT
from database import models
from bot.keyboards import back_menu_kb

router = Router()


@router.callback_query(F.data == "contact")
async def contact(c: CallbackQuery):
    if await models.is_technical_mode():
        await c.message.answer(TECH_TEXT, parse_mode="HTML")
        return await c.answer()

    await c.message.answer(
        CONTACT_TEXT, parse_mode="HTML", reply_markup=back_menu_kb(), disable_web_page_preview=True
    )
    await c.answer()
