import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db import init_db
from handlers.start import router as start_router
from handlers.games import router as games_router
async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    init_db()
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )
    dp = Dispatcher(
        storage=MemoryStorage()
    )
    dp.include_router(start_router)
    dp.include_router(games_router)
    logging.info("🎮 GAME EXCHANGE BOT запущен")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())