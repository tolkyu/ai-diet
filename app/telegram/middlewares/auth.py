from collections.abc import Awaitable, Callable
from typing import Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from app.database.session import AsyncSessionLocal
from app.services.user_service import UserService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Injects authenticated user and services into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract telegram user from any update type
        tg_user = None
        if isinstance(event, Update):
            if event.message:
                tg_user = event.message.from_user
            elif event.callback_query:
                tg_user = event.callback_query.from_user

        if tg_user:
            async with AsyncSessionLocal() as session:
                from app.services.food_log_service import FoodLogService
                user_service = UserService(session)
                food_log_service = FoodLogService(session)
                user, _ = await user_service.get_or_create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                )
                await session.commit()
                data["current_user"] = user
                data["user_service"] = user_service
                data["food_log_service"] = food_log_service
                result = await handler(event, data)
                await session.commit()
                return result

        return await handler(event, data)
