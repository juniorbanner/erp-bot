import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.auth import AuthMiddleware
from bot.handlers.client import profile, balance, orders
from bot.handlers.admin import nasiya, products, analytics, broadcast
from db.base import engine, Base
from db.models import *  # noqa: F401, F403 - import all models for alembic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    """Initialize database tables and set admin users."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-set admins from config
    if settings.admin_ids_list:
        from db.base import AsyncSessionFactory
        from db.models.user import User
        from sqlalchemy import update
        async with AsyncSessionFactory() as session:
            await session.execute(
                update(User)
                .where(User.id.in_(settings.admin_ids_list))
                .values(is_admin=True)
            )
            await session.commit()
        logger.info(f"Admin IDs set: {settings.admin_ids_list}")

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")


async def on_shutdown(bot: Bot):
    logger.info("Bot shutting down...")
    await bot.session.close()


async def main():
    bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)

    # Use Redis if available, fallback to Memory
    try:
        storage = RedisStorage.from_url(settings.REDIS_URL)
        logger.info("Using Redis FSM storage")
    except Exception:
        storage = MemoryStorage()
        logger.warning("Redis unavailable, using in-memory FSM storage")

    dp = Dispatcher(storage=storage)

    # ─── Middlewares ───────────────────────────────────────────────────────
    dp.update.middleware(DbSessionMiddleware())
    dp.update.middleware(AuthMiddleware())

    # ─── Register routers ──────────────────────────────────────────────────
    # Client handlers
    dp.include_router(profile.router)
    dp.include_router(balance.router)
    dp.include_router(orders.router)

    # Admin handlers
    dp.include_router(nasiya.router)
    dp.include_router(products.router)
    dp.include_router(analytics.router)
    dp.include_router(broadcast.router)

    # ─── Lifecycle hooks ───────────────────────────────────────────────────
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
