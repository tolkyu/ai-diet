from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request
from app.core.config import settings
from app.core.logging import get_logger
from app.telegram.bot import bot, dp

router = APIRouter()
logger = get_logger(__name__)


@router.post("/webhook/{token}")
async def telegram_webhook(
    token: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if token != settings.telegram_bot_token:
        raise HTTPException(status_code=403, detail="Invalid token")

    if (
        settings.telegram_webhook_secret
        and x_telegram_bot_api_secret_token != settings.telegram_webhook_secret
    ):
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    body = await request.json()
    update = Update.model_validate(body, context={"bot": bot})

    try:
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error("Error processing update", error=str(e), update_id=body.get("update_id"))

    return {"ok": True}
