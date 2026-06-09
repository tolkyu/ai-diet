from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.telegram.states.forms import RegistrationStates
from app.telegram.keyboards.inline import (
    gender_keyboard,
    activity_keyboard,
    main_menu_keyboard,
)
from app.telegram.keyboards.reply import main_reply_keyboard
from app.core.logging import get_logger
from app.i18n.ua import (
    START_WELCOME, START_WELCOME_BACK,
    START_CHOOSE_GENDER, START_GOT_GENDER_M, START_GOT_GENDER_F,
    START_INVALID_AGE, START_GOT_AGE,
    START_INVALID_HEIGHT, START_GOT_HEIGHT,
    START_INVALID_WEIGHT, START_GOT_WEIGHT,
    START_CHOOSE_ACTIVITY, START_PROFILE_SAVED, MAIN_MENU_BUTTONS,
)

router = Router(name="start")
logger = get_logger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_service) -> None:
    user = message.from_user
    if not user:
        return

    tg_user, created = await user_service.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    if tg_user.is_registered:
        await message.answer(
            START_WELCOME_BACK.format(name=tg_user.display_name),
            reply_markup=main_reply_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        START_WELCOME.format(name=user.first_name or "друже"),
        reply_markup=gender_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_for_gender)


@router.callback_query(RegistrationStates.waiting_for_gender, F.data.startswith("gender:"))
async def handle_gender(callback: CallbackQuery, state: FSMContext) -> None:
    gender = callback.data.split(":")[1]  # type: ignore[union-attr]
    await state.update_data(gender=gender)
    text = START_GOT_GENDER_M if gender == "male" else START_GOT_GENDER_F
    await callback.message.edit_text(text)  # type: ignore[union-attr]
    await state.set_state(RegistrationStates.waiting_for_age)
    await callback.answer()


@router.message(RegistrationStates.waiting_for_age, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_age(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text.strip())  # type: ignore[union-attr]
        if not 13 <= age <= 100:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(START_INVALID_AGE)
        return

    await state.update_data(age=age)
    await message.answer(START_GOT_AGE.format(age=age))
    await state.set_state(RegistrationStates.waiting_for_height)


@router.message(RegistrationStates.waiting_for_height, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_height(message: Message, state: FSMContext) -> None:
    try:
        height = float(message.text.strip().replace(",", "."))  # type: ignore[union-attr]
        if not 100 <= height <= 250:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(START_INVALID_HEIGHT)
        return

    await state.update_data(height_cm=height)
    await message.answer(START_GOT_HEIGHT.format(height=height))
    await state.set_state(RegistrationStates.waiting_for_weight)


@router.message(RegistrationStates.waiting_for_weight, ~F.text.in_(MAIN_MENU_BUTTONS))
async def handle_weight(message: Message, state: FSMContext) -> None:
    try:
        weight = float(message.text.strip().replace(",", "."))  # type: ignore[union-attr]
        if not 30 <= weight <= 300:
            raise ValueError
    except (ValueError, AttributeError):
        await message.answer(START_INVALID_WEIGHT)
        return

    await state.update_data(weight_kg=weight)
    await message.answer(
        START_GOT_WEIGHT.format(weight=weight),
        reply_markup=activity_keyboard(),
    )
    await state.set_state(RegistrationStates.waiting_for_activity)


@router.callback_query(RegistrationStates.waiting_for_activity, F.data.startswith("activity:"))
async def handle_activity(
    callback: CallbackQuery, state: FSMContext, user_service
) -> None:
    activity = callback.data.split(":")[1]  # type: ignore[union-attr]
    data = await state.get_data()

    await user_service.complete_registration(
        telegram_id=callback.from_user.id,
        gender=data["gender"],
        age=data["age"],
        height_cm=data["height_cm"],
        weight_kg=data["weight_kg"],
        activity_level=activity,
    )

    await callback.message.edit_text(START_PROFILE_SAVED)  # type: ignore[union-attr]
    await state.clear()

    from app.telegram.keyboards.inline import goal_type_keyboard
    from app.i18n.ua import GOAL_CHOOSE
    await callback.message.answer(GOAL_CHOOSE, reply_markup=goal_type_keyboard())  # type: ignore[union-attr]
    from app.telegram.states.forms import GoalStates
    await state.set_state(GoalStates.waiting_for_goal_type)
    await callback.answer()
