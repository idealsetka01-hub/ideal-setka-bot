# -*- coding: utf-8 -*-
"""
Aiogram Bot obyektini butun loyiha bo'ylab (bot handlerlari va FastAPI server)
bitta joydan ulashish uchun. main.py ishga tushganda set_bot() chaqiriladi.
"""
bot = None


def set_bot(bot_instance):
    global bot
    bot = bot_instance


def get_bot():
    if bot is None:
        raise RuntimeError("Bot hali ishga tushirilmagan (bot_instance.set_bot chaqirilmagan)")
    return bot
