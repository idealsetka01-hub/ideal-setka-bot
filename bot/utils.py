# -*- coding: utf-8 -*-
"""Matn formatlash uchun umumiy yordamchi funksiyalar."""


def format_price(price) -> str:
    if price is None:
        return "aniqlanmagan"
    return f"{price:,}".replace(",", " ") + " so‘m"


def product_short_label(p) -> str:
    parts = []
    if p["wire"]:
        parts.append(p["wire"])
    if p["cell"]:
        parts.append(p["cell"])
    if p["size"]:
        parts.append(p["size"])
    if p["spec"]:
        parts.append(p["spec"])
    label = " | ".join(parts) if parts else (p["name"] or f"#{p['id']}")
    if p["name"] and parts:
        label = f"{p['name']} | {label}"
    return label


def product_full_description(p) -> str:
    extra = []
    if p["wire"]:
        extra.append(p["wire"])
    if p["cell"]:
        extra.append(p["cell"])
    if p["size"]:
        extra.append(p["size"])
    if p["spec"]:
        extra.append(p["spec"])
    name = p["name"] or ""
    body = " | ".join(extra)
    if name:
        body = f"{body}{' | ' + name if body else name}"
    return body


def only_int_or_none(text: str):
    """Faqat butun sonlarni qabul qiladi. Kasr yoki bo'sh matnda None qaytaradi."""
    text = (text or "").strip()
    if not text.isdigit():
        return None
    value = int(text)
    return value if value > 0 else None
