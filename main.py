# -*- coding: utf-8 -*-
import asyncio

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, WEBAPP_PORT
from database.db import init_db
from bot import bot_instance
from bot.handlers import routers
from server import app as fastapi_app

dp = Dispatcher(storage=MemoryStorage())
for r in routers:
    dp.include_router(r)


async def run_server():
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=WEBAPP_PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env yoki Replit/Render Secrets ga kiritilmagan")

    await init_db()

    bot = Bot(BOT_TOKEN)
    bot_instance.set_bot(bot)  # FastAPI serverga ham shu bot obyekti ko'rinishi uchun avval o'rnatiladi
    await bot.delete_webhook(drop_pending_updates=True)

    # Bot polling va FastAPI (Mini App backend) bitta process ichida, parallel ishlaydi.
    # Bu Replit/Render kabi bitta port/bitta process talab qiladigan muhitlar uchun qulay.
    await asyncio.gather(dp.start_polling(bot), run_server())


if __name__ == "__main__":
    asyncio.run(main())
