import time
from collections.abc import Awaitable, Callable
from typing import Any
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        start = time.monotonic()
        user_id = None
        event_type = type(event).__name__

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            logger.info(
                "Telegram message",
                event_type="message",
                telegram_id=user_id,
                content_type=event.content_type,
            )
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            logger.info(
                "Telegram callback",
                event_type="callback",
                telegram_id=user_id,
                data=event.data,
            )

        try:
            result = await handler(event, data)
            elapsed = (time.monotonic() - start) * 1000
            logger.debug(
                "Handler completed",
                event_type=event_type,
                telegram_id=user_id,
                elapsed_ms=round(elapsed, 1),
            )
            return result
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            logger.error(
                "Handler error",
                event_type=event_type,
                telegram_id=user_id,
                error=str(e),
                elapsed_ms=round(elapsed, 1),
            )
            raise
