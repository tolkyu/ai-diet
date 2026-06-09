"""
Development runner — polling mode (no webhook, no Docker needed).
Requires only: TELEGRAM_BOT_TOKEN and OPENAI_API_KEY in .env
Uses in-memory SQLite so no PostgreSQL needed for local testing.
"""
import asyncio
import os
import sys

# Patch DATABASE_URL to SQLite before any app imports
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_DEBUG", "true")

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.telegram.handlers import start, goal, dashboard, food_log, weight, stats, profile, help, upgrade, subscribe, water
from app.telegram.middlewares.auth import AuthMiddleware
from app.telegram.middlewares.logging import LoggingMiddleware

logger = get_logger(__name__)


async def create_tables() -> None:
    """Create SQLite tables on startup."""
    from app.database.base import Base
    from app.database.session import engine
    import app.models  # noqa — registers all models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def main() -> None:
    configure_logging()
    logger.info("Starting @diet_ss_bot in polling mode", token_prefix=settings.telegram_bot_token[:10])

    # Override DATABASE_URL to SQLite for local dev
    from app.core import config as cfg
    cfg.settings.database_url = "sqlite+aiosqlite:///./dev.db"  # type: ignore

    await create_tables()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

    # Register all handlers
    dp.include_router(start.router)
    dp.include_router(goal.router)
    dp.include_router(dashboard.router)
    dp.include_router(food_log.router)
    dp.include_router(weight.router)
    dp.include_router(stats.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    dp.include_router(upgrade.router)
    dp.include_router(subscribe.router)
    dp.include_router(water.router)

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")

    # Register bot commands visible in Telegram UI
    from aiogram.types import BotCommand, BotCommandScopeDefault
    await bot.set_my_commands([
        BotCommand(command="start",     description="Почати / скинути налаштування"),
        BotCommand(command="dashboard", description="Прогрес за сьогодні"),
        BotCommand(command="logfood",   description="Записати прийом їжі"),
        BotCommand(command="weight",    description="Записати вагу"),
        BotCommand(command="goal",      description="Змінити ціль"),
        BotCommand(command="stats",     description="Тижнева статистика"),
        BotCommand(command="profile",   description="Мій профіль"),
        BotCommand(command="help",      description="Допомога"),
        BotCommand(command="subscribe", description="Преміум підписка"),
        BotCommand(command="water",     description="Відстеження води (Преміум)"),
    ], scope=BotCommandScopeDefault())

    print(f"\nBot @{me.username} is running in polling mode!")
    print("   Open Telegram and message your bot to test it.")
    print("   Press Ctrl+C to stop.\n")

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "pre_checkout_query"],
            drop_pending_updates=True,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
