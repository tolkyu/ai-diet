from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from app.core.config import settings
from app.core.logging import get_logger
from app.telegram.middlewares.auth import AuthMiddleware
from app.telegram.middlewares.logging import LoggingMiddleware
from app.telegram.middlewares.rate_limit import RateLimitMiddleware
from app.telegram.handlers import start, goal, dashboard, food_log, weight, stats, profile, help, upgrade, subscribe, water, admin

logger = get_logger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Middlewares (order matters — first applied = outermost)
    dp.update.outer_middleware(LoggingMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    # Register all routers
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

    logger.info("Bot dispatcher configured with all handlers")
    return dp


bot = create_bot()
dp = create_dispatcher()
