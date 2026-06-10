"""
Production runner — polling mode with PostgreSQL + Redis.
Used for Railway deployment (no webhook, no uvicorn needed).
"""
import asyncio
import sys

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.telegram.handlers import start, goal, dashboard, food_log, weight, stats, profile, help, upgrade, subscribe, water, admin
from app.telegram.middlewares.auth import AuthMiddleware
from app.telegram.middlewares.logging import LoggingMiddleware

logger = get_logger(__name__)


async def run_migrations() -> None:
    from alembic.config import Config
    from alembic import command
    import threading

    def _run():
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run)
    logger.info("Migrations applied")


async def main() -> None:
    configure_logging()
    logger.info("Starting bot in production polling mode")

    await run_migrations()

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(AuthMiddleware())

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
    dp.include_router(admin.router)

    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username}")

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

    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "pre_checkout_query"],
            drop_pending_updates=False,
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except Exception as e:
        print(f"[crash] Bot crashed: {e}", flush=True)
        sys.exit(1)
