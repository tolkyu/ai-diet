import sentry_sdk
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.database.base import Base
from app.database.session import engine
from app.routers import webhook, health, admin

logger = get_logger(__name__)


def setup_sentry() -> None:
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            traces_sample_rate=0.1,
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    setup_sentry()
    logger.info("Starting AI Diet Bot", env=settings.app_env)

    # Create tables in development; use Alembic in production
    if not settings.is_production:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Register webhook with Telegram
    if settings.telegram_webhook_url and settings.is_production:
        from app.telegram.bot import bot
        webhook_url = f"{settings.telegram_webhook_url}{settings.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram_webhook_secret,
            allowed_updates=["message", "callback_query"],
        )
        logger.info("Webhook registered", url=webhook_url)

    yield

    logger.info("Shutting down AI Diet Bot")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Nutrition Coach",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["POST", "GET"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(webhook.router, prefix="/api/v1", tags=["webhook"])
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])

    # Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_app()
