# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import TECH_TEXT
from database import models
from bot.keyboards import main_menu_kb

router = Router()


async def _tech_blocked(answer_target) -> bool:
    if await models.is_technical_mode():
        await answer_target.answer(TECH_TEXT, parse_mode="HTML")
        return True
    return False


@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    if await _tech_blocked(m):
        return

    await models.upsert_user(
        telegram_id=m.from_user.id,
        username=m.from_user.username,
        full_name=m.from_user.full_name,
    )

    categories = await models.get_categories()
    webapp_enabled = await models.is_webapp_enabled()

    # Mavjud /start xush kelibsiz matni saqlangan, faqat AI haqida qisqa eslatma qo'shildi.
    await m.answer(
        "Assalomu alaykum! 👋\n\n"
        "IDEAL SETKA botiga xush kelibsiz.\n\n"
        "💬 Savolingiz bo‘lsa, shunchaki yozib yuboring — AI yordamchimiz javob beradi.",
        reply_markup=main_menu_kb(categories, webapp_enabled=webapp_enabled),
    )


@router.callback_query(F.data == "back_menu")
async def back_to_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()
    if await _tech_blocked(c.message):
        return await c.answer()

    categories = await models.get_categories()
    webapp_enabled = await models.is_webapp_enabled()
    await c.message.answer("Bosh menyu:", reply_markup=main_menu_kb(categories, webapp_enabled=webapp_enabled))
    await c.answer()
