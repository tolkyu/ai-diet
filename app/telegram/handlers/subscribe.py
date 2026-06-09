from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery, LabeledPrice, Message, PreCheckoutQuery, SuccessfulPayment,
)
from app.core.config import settings
from app.core.logging import get_logger
from app.i18n.ua import (
    SUBSCRIBE_PLANS, SUBSCRIBE_SUCCESS, SUBSCRIBE_ALREADY_PREMIUM, SUBSCRIBE_CANCELLED,
    SUBSCRIBE_INVOICE_MONTHLY_TITLE, SUBSCRIBE_INVOICE_MONTHLY_DESC,
    SUBSCRIBE_INVOICE_YEARLY_TITLE, SUBSCRIBE_INVOICE_YEARLY_DESC,
)

router = Router(name="subscribe")
logger = get_logger(__name__)

_PAYLOAD_MONTHLY = "premium_monthly"
_PAYLOAD_YEARLY  = "premium_yearly"


def _subscribe_keyboard():
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from app.i18n.ua import SUBSCRIBE_BTN_MONTHLY, SUBSCRIBE_BTN_YEARLY, SUBSCRIBE_BTN_CANCEL
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=SUBSCRIBE_BTN_MONTHLY, callback_data="sub:monthly"))
    builder.add(InlineKeyboardButton(text=SUBSCRIBE_BTN_YEARLY,  callback_data="sub:yearly"))
    builder.add(InlineKeyboardButton(text=SUBSCRIBE_BTN_CANCEL,  callback_data="sub:cancel"))
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.subscription_service import SubscriptionService

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_svc = SubscriptionService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if not user:
            await message.answer("Спочатку налаштуй профіль через /start.")
            return
        sub_info = await sub_svc.get_usage_info(user.id)

    if sub_info["plan"] == "premium":
        await message.answer(SUBSCRIBE_ALREADY_PREMIUM)
        return

    await message.answer(SUBSCRIBE_PLANS, parse_mode="HTML", reply_markup=_subscribe_keyboard())


@router.callback_query(F.data == "sub:monthly")
async def handle_sub_monthly(callback: CallbackQuery) -> None:
    await callback.message.delete()  # type: ignore[union-attr]
    await callback.bot.send_invoice(  # type: ignore[union-attr]
        chat_id=callback.from_user.id,
        title=SUBSCRIBE_INVOICE_MONTHLY_TITLE,
        description=SUBSCRIBE_INVOICE_MONTHLY_DESC,
        payload=_PAYLOAD_MONTHLY,
        currency="XTR",
        prices=[LabeledPrice(label="Преміум · 1 місяць", amount=settings.stars_monthly_price)],
    )
    await callback.answer()


@router.callback_query(F.data == "sub:yearly")
async def handle_sub_yearly(callback: CallbackQuery) -> None:
    await callback.message.delete()  # type: ignore[union-attr]
    await callback.bot.send_invoice(  # type: ignore[union-attr]
        chat_id=callback.from_user.id,
        title=SUBSCRIBE_INVOICE_YEARLY_TITLE,
        description=SUBSCRIBE_INVOICE_YEARLY_DESC,
        payload=_PAYLOAD_YEARLY,
        currency="XTR",
        prices=[LabeledPrice(label="Преміум · 1 рік", amount=settings.stars_yearly_price)],
    )
    await callback.answer()


@router.callback_query(F.data == "sub:cancel")
async def handle_sub_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text(SUBSCRIBE_CANCELLED)  # type: ignore[union-attr]
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout: PreCheckoutQuery) -> None:
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.payment_service import PaymentService

    payment: SuccessfulPayment = message.successful_payment  # type: ignore[assignment]
    payload = payment.invoice_payload
    months = 12 if payload == _PAYLOAD_YEARLY else 1
    plan_label = "yearly" if payload == _PAYLOAD_YEARLY else "monthly"
    stars = payment.total_amount

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        payment_svc = PaymentService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if not user:
            return
        await payment_svc.handle_successful_payment(
            user_id=user.id,
            transaction_id=payment.telegram_payment_charge_id,
            stars_amount=stars,
            plan=plan_label,
            subscription_months=months,
        )
        await session.commit()

    logger.info("Payment processed", telegram_id=message.from_user.id, stars=stars, plan=plan_label)  # type: ignore[union-attr]
    await message.answer(SUBSCRIBE_SUCCESS, parse_mode="HTML")
