# -*- coding: utf-8 -*-
"""
Har qanday erkin matnli xabar (boshqa hech qaysi holat/komandaga to'g'ri kelmasa)
shu yerga tushadi va AI yordamchi javob beradi. AI mumkin qadar keng va foydali
javob berishga harakat qiladi, lekin mahsulot/narx haqida gap ketganda faqat
bazadagi haqiqiy ma'lumotlarga tayanadi (hech narsani o'zidan to'qib chiqarmaydi).
"""
import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import TECH_TEXT, AI_API_KEY, AI_MODEL, CONTACT_TEXT, DELIVERY_TEXT
from database import models
from bot.keyboards import back_menu_kb
from bot.utils import product_full_description, format_price

router = Router()

_CONTACT_KEYWORDS = ("aloqa", "telefon", "manzil", "address", "contact", "qayerda", "ish vaqti")

_SYSTEM_BASE = (
    "Sen IDEAL SETKA kompaniyasining Telegram botidagi AI yordamchisisan. "
    "IDEAL SETKA — setka, panjara va zabor mahsulotlari ishlab chiqaruvchi/sotuvchi korxona.\n\n"
    "QOIDALAR:\n"
    "1) Mahsulot, narx yoki razmer haqida gapirganda FAQAT quyida berilgan mahsulot ma'lumotlariga "
    "asoslan. Hech qanday narx, razmer yoki mahsulotni o'zingdan to'qib chiqarma.\n"
    "2) Mijozning boshqa (mahsulotga bevosita aloqasi bo'lmagan) savollariga ham iloji boricha keng, "
    "foydali va samimiy javob ber — masalan qurilish, montaj, maslahat, umumiy savollar. Bunday "
    "holatlarda o'zingning bilimingdan erkin foydalanishing mumkin, faqat IDEAL SETKA'ning o'z "
    "mahsulot/narxlari haqida gap ketmasa.\n"
    "3) Agar kerakli mahsulot bazada topilmasa yoki narxi hali belgilanmagan bo'lsa, buni ochiq ayt "
    "va operator bilan bog'lanishni tavsiya qil.\n"
    "4) Javobni o'zbek tilida, tabiiy va do'stona ohangda yoz — juda qisqa yoki quruq bo'lmasin, "
    "lekin ortiqcha cho'zib ham yubormas.\n\n"
    f"🚚 Yetkazib berish barcha mahsulotlar uchun: {DELIVERY_TEXT}\n\n"
    f"Kontaktlar:\n{CONTACT_TEXT}"
)


def _format_catalog(rows) -> str:
    lines, current_cat = [], None
    for p in rows:
        if p["category_name"] != current_cat:
            current_cat = p["category_name"]
            lines.append(f"\n### {current_cat}")
        desc = product_full_description(p)
        price_txt = format_price(p["price"])
        lines.append(f"- {desc} — {price_txt} — {p['unit']}")
    return "\n".join(lines)


async def _ask_ai_model(query: str, catalog_text: str) -> str:
    import anthropic

    system_prompt = f"{_SYSTEM_BASE}\n\nTO‘LIQ MAHSULOT BAZASI:\n{catalog_text}"

    def _call():
        client = anthropic.Anthropic(api_key=AI_API_KEY)
        resp = client.messages.create(
            model=AI_MODEL,
            max_tokens=600,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    return await asyncio.to_thread(_call)


def _keyword_search(rows, query: str, limit: int = 15):
    tokens = [t for t in query.lower().replace("×", "x").split() if len(t) >= 2]
    if not tokens:
        return []
    matches = []
    for p in rows:
        haystack = " ".join(
            str(v) for v in [p["category_name"], p["name"], p["wire"], p["cell"], p["size"], p["spec"]] if v
        ).lower().replace("×", "x")
        if any(tok in haystack for tok in tokens):
            matches.append(p)
    return matches[:limit]


def _format_matches(matches) -> str:
    lines = []
    for p in matches:
        desc = product_full_description(p)
        price_txt = format_price(p["price"])
        lines.append(f"• {p['category_name']}: {desc} — {price_txt} — {p['unit']}")
    return "\n".join(lines)


@router.message(F.text, ~F.text.startswith("/"))
async def ai_catch_all(m: Message, state: FSMContext):
    # Bu handler faqat FSM holati bo'lmagan (boshqa hech bir aniq bosqichga tegishli
    # bo'lmagan) erkin matnli xabarlar uchun ishlaydi — chunki u routerlar ro'yxatida
    # eng oxirida turadi va aniqroq filterli handlerlar avval tekshiriladi.
    if await models.is_technical_mode():
        return await m.answer(TECH_TEXT, parse_mode="HTML")

    query = (m.text or "").strip()
    if not query:
        return

    if any(k in query.lower() for k in _CONTACT_KEYWORDS):
        await m.answer(CONTACT_TEXT, parse_mode="HTML", reply_markup=back_menu_kb())
        return

    rows = await models.get_all_active_products()

    if AI_API_KEY:
        try:
            catalog_text = _format_catalog(rows)
            answer = await _ask_ai_model(query, catalog_text)
            if answer.strip():
                await m.answer(answer.strip(), reply_markup=back_menu_kb())
                return
        except Exception:
            pass  # API mavjud bo'lmasa/xato bo'lsa — oddiy qidiruvga o'tamiz

    matches = _keyword_search(rows, query)
    if matches:
        text = "🔎 Topilgan mahsulotlar:\n\n" + _format_matches(matches)
    else:
        text = (
            "🔎 IDEAL SETKA mahsulotlari bo‘yicha savolingizni yozing — masalan mahsulot nomi, "
            "razmeri yoki kategoriyasini kiriting.\n\n"
            "Kerak bo‘lsa, quyidagi menyudan kategoriyani tanlashingiz yoki operatorlarimizga "
            "murojaat qilishingiz mumkin:\n\n" + CONTACT_TEXT
        )
    await m.answer(text, parse_mode="HTML", reply_markup=back_menu_kb())
