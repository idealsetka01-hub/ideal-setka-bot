# -*- coding: utf-8 -*-
from bot.handlers import admin, start, contact, catalog, order, ai

# Muhim: ai.router eng oxirida bo'lishi shart — u state'ga bog'liq bo'lmagan
# "catch-all" xabar handler'ini o'z ichiga oladi (erkin matn savollarga AI javob beradi).
# Shu sababli avval boshqa barcha aniq holat/komanda handlerlari tekshiriladi.
routers = [
    admin.router,
    start.router,
    contact.router,
    catalog.router,
    order.router,
    ai.router,
]
