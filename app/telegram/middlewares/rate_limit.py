from collections.abc import Awaitable, Callable
from typing import Any
import redis.asyncio as aioredis
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Separate Redis connection for rate limiting
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


class RateLimitMiddleware(BaseMiddleware):
    """Per-user rate limiting using Redis sliding window."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        try:
            redis = await get_redis()
            key = f"rate:{user.id}:messages"
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, 60)  # 1 minute window

            if count > settings.rate_limit_messages_per_minute:
                logger.warning("Rate limit exceeded", telegram_id=user.id, count=count)
                await event.answer(
                    "⚠️ You're sending messages too fast. Please wait a moment."
                )
                return None
        except Exception as e:
            logger.warning("Rate limit check failed", error=str(e))

        return await handler(event, data)
