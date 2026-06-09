from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.core.config import settings
from app.core.logging import get_logger
from app.i18n.ua import UPGRADE_ALREADY_PREMIUM, UPGRADE_SUCCESS, UPGRADE_NOT_AUTHORIZED

router = Router(name="upgrade")
logger = get_logger(__name__)


def _is_admin(telegram_id: int) -> bool:
    if not settings.admin_telegram_ids:
        return False
    ids = [i.strip() for i in settings.admin_telegram_ids.split(",") if i.strip()]
    return str(telegram_id) in ids


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.subscription_service import SubscriptionService

    telegram_id = message.from_user.id  # type: ignore[union-attr]

    if not _is_admin(telegram_id):
        await message.answer(UPGRADE_NOT_AUTHORIZED, parse_mode="HTML")
        return

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_svc = SubscriptionService(session)

        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            await message.answer("Спочатку налаштуй профіль через /start.")
            return

        sub = await sub_svc.get_subscription(user.id)
        if sub.is_premium:
            await message.answer(UPGRADE_ALREADY_PREMIUM)
            return

        await sub_svc.upgrade_to_premium(user.id)
        await session.commit()

    logger.info("User upgraded to premium", telegram_id=telegram_id)
    await message.answer(UPGRADE_SUCCESS, parse_mode="HTML")
