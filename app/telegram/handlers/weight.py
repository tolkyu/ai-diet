from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.telegram.states.forms import WeightStates
from app.telegram.keyboards.inline import main_menu_keyboard, skip_keyboard
from app.core.logging import get_logger
from app.i18n.ua import (
    WEIGHT_PROMPT, WEIGHT_GOT_WEIGHT, WEIGHT_INVALID, WEIGHT_INVALID_FAT,
    WEIGHT_SAVED, WEIGHT_FAT_LINE, WEIGHT_TREND_LINE, WEIGHT_FAT_PREMIUM_TIP,
    BTN_WEIGHT, MAIN_MENU_BUTTONS,
)

router = Router(name="weight")
logger = get_logger(__name__)


@router.message(Command("weight"))
@router.message(F.text == BTN_WEIGHT)
@router.callback_query(F.data == "menu:weight")
async def cmd_weight(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(WeightStates.waiting_for_weight)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(WEIGHT_PROMPT, parse_mode="HTML")  # type: ignore[union-attr]
        await event.answer()
    else:
        await event.answer(WEIGHT_PROMPT, parse_mode="HTML")


@router.message(WeightStates.waiting_for_weight, F.text, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_weight_input(message: Message, state: FSMContext) -> None:
    try:
        weight = float(message.text.strip().replace(",", "."))  # type: ignore[union-attr]
        if not 30 <= weight <= 300:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(WEIGHT_INVALID)
        return

    await state.update_data(weight_kg=weight)

    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.subscription_service import SubscriptionService

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_svc = SubscriptionService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if user:
            sub_info = await sub_svc.get_usage_info(user.id, telegram_id=message.from_user.id)  # type: ignore[union-attr]
            is_premium = sub_info["plan"] == "premium"
        else:
            is_premium = False

    if not is_premium:
        await state.update_data(weight_kg=weight)
        await _save_weight(message, state, body_fat=None, premium_tip=True)
        return

    await message.answer(
        WEIGHT_GOT_WEIGHT.format(weight=weight),
        reply_markup=skip_keyboard("weight:skip_fat"),
    )
    await state.set_state(WeightStates.waiting_for_body_fat)


@router.callback_query(WeightStates.waiting_for_body_fat, F.data == "weight:skip_fat")
async def skip_body_fat(callback: CallbackQuery, state: FSMContext) -> None:
    await _save_weight(callback, state, body_fat=None)


@router.message(WeightStates.waiting_for_body_fat, F.text, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_body_fat(message: Message, state: FSMContext) -> None:
    try:
        body_fat = float(message.text.strip().replace(",", "."))  # type: ignore[union-attr]
        if not 3 <= body_fat <= 70:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(WEIGHT_INVALID_FAT)
        return
    await _save_weight(message, state, body_fat=body_fat)


async def _save_weight(
    event: Message | CallbackQuery, state: FSMContext, body_fat: float | None, premium_tip: bool = False
) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.weight_service import WeightService

    data = await state.get_data()
    weight = data["weight_kg"]
    telegram_id = event.from_user.id  # type: ignore[union-attr]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        weight_svc = WeightService(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return

        await weight_svc.log_weight(user.id, weight, body_fat)
        trend = await weight_svc.get_trend(user.id)
        await session.commit()

    trend_line = ""
    if trend["num_entries"] > 1:
        change = trend["change_kg"]
        arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        trend_line = WEIGHT_TREND_LINE.format(arrow=arrow, change=change)

    fat_line = WEIGHT_FAT_LINE.format(fat=body_fat) if body_fat else ""
    tip_line = WEIGHT_FAT_PREMIUM_TIP if premium_tip else ""

    text = WEIGHT_SAVED.format(weight=weight, fat_line=fat_line, trend_line=trend_line) + tip_line

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())

    await state.clear()
