import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import settings
from database.db import init_db
from middlewares.rate_limit import RateLimitMiddleware

from handlers import start, check, coffee, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start",  description="Начать"),
        BotCommand(command="help",   description="Как пользоваться"),
        BotCommand(command="coffee", description="Поддержать разработку ☕"),
    ]
    await bot.set_my_commands(commands)


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(RateLimitMiddleware())

    # Роутеры — порядок важен: catch-all (check) идёт последним
    dp.include_router(start.router)
    dp.include_router(coffee.router)
    dp.include_router(admin.router)
    dp.include_router(check.router)   # ← last, содержит F.text

    await init_db()
    await set_commands(bot)

    logger.info("PassGuard Bot запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
