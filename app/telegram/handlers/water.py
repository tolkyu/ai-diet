from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.core.logging import get_logger
from app.i18n.ua import (
    WATER_PREMIUM_ONLY, WATER_PROMPT, WATER_INVALID,
    WATER_GOAL_REACHED, BTN_WATER_250, BTN_WATER_350, BTN_WATER_500,
    BTN_WATER_CUSTOM, BTN_WATER, MAIN_MENU_BUTTONS,
)

router = Router(name="water")
logger = get_logger(__name__)

BAR_FILLED = "█"
BAR_EMPTY  = "░"
BAR_LEN    = 10


class WaterStates(StatesGroup):
    waiting_for_custom_ml = State()


def _water_keyboard() -> object:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=BTN_WATER_250,  callback_data="water:250"),
        InlineKeyboardButton(text=BTN_WATER_350,  callback_data="water:350"),
        InlineKeyboardButton(text=BTN_WATER_500,  callback_data="water:500"),
        InlineKeyboardButton(text=BTN_WATER_CUSTOM, callback_data="water:custom"),
    )
    builder.adjust(3, 1)
    return builder.as_markup()


def _water_bar(current: int, goal: int) -> str:
    pct = min(current / goal, 1.0)
    filled = round(pct * BAR_LEN)
    return BAR_FILLED * filled + BAR_EMPTY * (BAR_LEN - filled)


async def _show_water_dashboard(event: Message | CallbackQuery, state: FSMContext, added_ml: int | None = None) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.water_service import WaterService

    telegram_id = event.from_user.id  # type: ignore[union-attr]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        water_svc = WaterService(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return
        log = await water_svc.get_today_log(user.id)
        await session.commit()

    pct = (log.total_ml / log.goal_ml * 100) if log.goal_ml else 0
    bar = _water_bar(log.total_ml, log.goal_ml)

    success_note = f"✅ Записано +{added_ml}мл\n\n" if added_ml else ""
    goal_note = f"\n\n{WATER_GOAL_REACHED}" if (added_ml and log.total_ml >= log.goal_ml) else ""
    text = success_note + WATER_PROMPT.format(current=log.total_ml, goal=log.goal_ml, bar=bar, pct=pct) + goal_note

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=_water_keyboard())  # type: ignore[union-attr]
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=_water_keyboard())


@router.message(Command("water"))
@router.message(F.text == BTN_WATER)
async def cmd_water(message: Message, state: FSMContext) -> None:
    await state.clear()

    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.subscription_service import SubscriptionService
    from app.telegram.keyboards.inline import main_menu_keyboard

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_svc = SubscriptionService(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if not user:
            await message.answer("Спочатку налаштуй профіль через /start.")
            return
        sub_info = await sub_svc.get_usage_info(user.id)

    if sub_info["plan"] != "premium":
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="⭐ Отримати Преміум", callback_data="go:subscribe"))
        await message.answer(WATER_PREMIUM_ONLY, parse_mode="HTML", reply_markup=builder.as_markup())
        return

    await _show_water_dashboard(message, state)


@router.callback_query(F.data.startswith("water:"))
async def handle_water_add(callback: CallbackQuery, state: FSMContext) -> None:
    amount_str = callback.data.split(":")[1]  # type: ignore[union-attr]

    if amount_str == "custom":
        await callback.message.edit_text("💧 Введи кількість мл (наприклад: 300):")  # type: ignore[union-attr]
        await state.set_state(WaterStates.waiting_for_custom_ml)
        await callback.answer()
        return

    ml = int(amount_str)
    await _add_and_respond(callback, ml, state)


@router.message(WaterStates.waiting_for_custom_ml, F.text, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_custom_ml(message: Message, state: FSMContext) -> None:
    try:
        ml = int(message.text.strip())  # type: ignore[union-attr]
        if not 50 <= ml <= 2000:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(WATER_INVALID)
        return
    await state.clear()
    await _add_and_respond(message, ml, state)


async def _add_and_respond(event: Message | CallbackQuery, ml: int, state: FSMContext) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.water_service import WaterService

    telegram_id = event.from_user.id  # type: ignore[union-attr]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        water_svc = WaterService(session)
        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user:
            return
        await water_svc.add_water(user.id, ml)
        await session.commit()

    await _show_water_dashboard(event, state, added_ml=ml)


@router.callback_query(F.data == "go:subscribe")
async def go_to_subscribe(callback: CallbackQuery) -> None:
    from app.telegram.handlers.subscribe import cmd_subscribe
    await callback.message.delete()  # type: ignore[union-attr]
    await cmd_subscribe(callback.message)  # type: ignore[arg-type]
    await callback.answer()
