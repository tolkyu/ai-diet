from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.telegram.states.forms import GoalStates
from app.telegram.keyboards.inline import (
    goal_type_keyboard,
    weight_loss_intensity_keyboard,
    muscle_gain_intensity_keyboard,
    main_menu_keyboard,
)
from app.telegram.keyboards.reply import main_reply_keyboard
from app.core.constants import GoalType, GoalIntensity
from app.core.logging import get_logger
from app.i18n.ua import (
    GOAL_CHOOSE, GOAL_CHOOSE_NEW, GOAL_LOSE_INTENSITY, GOAL_MUSCLE_INTENSITY,
    GOAL_SET_TEXT, GOAL_SET_ANSWER, GOAL_MENU_HINT, GOAL_LABELS,
    GOAL_USER_NOT_FOUND,
)

router = Router(name="goal")
logger = get_logger(__name__)


@router.message(Command("goal"))
async def cmd_goal(message: Message, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_for_goal_type)
    await message.answer(GOAL_CHOOSE, reply_markup=goal_type_keyboard())


@router.callback_query(F.data == "menu:goal")
async def menu_goal(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GoalStates.waiting_for_goal_type)
    await callback.message.edit_text(GOAL_CHOOSE_NEW, reply_markup=goal_type_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(GoalStates.waiting_for_goal_type, F.data.startswith("goal:"))
async def handle_goal_type(callback: CallbackQuery, state: FSMContext) -> None:
    goal_type = callback.data.split(":")[1]  # type: ignore[union-attr]
    await state.update_data(goal_type=goal_type)

    if goal_type == GoalType.MAINTAIN:
        await state.update_data(intensity=None)
        await _finalize_goal(callback, state)
        return
    elif goal_type == GoalType.LOSE_WEIGHT:
        await callback.message.edit_text(  # type: ignore[union-attr]
            GOAL_LOSE_INTENSITY,
            parse_mode="HTML",
            reply_markup=weight_loss_intensity_keyboard(),
        )
    else:
        await callback.message.edit_text(  # type: ignore[union-attr]
            GOAL_MUSCLE_INTENSITY,
            parse_mode="HTML",
            reply_markup=muscle_gain_intensity_keyboard(),
        )

    await state.set_state(GoalStates.waiting_for_intensity)
    await callback.answer()


@router.callback_query(GoalStates.waiting_for_intensity, F.data.startswith("intensity:"))
async def handle_intensity(callback: CallbackQuery, state: FSMContext) -> None:
    intensity = callback.data.split(":")[1]  # type: ignore[union-attr]
    await state.update_data(intensity=intensity)
    await _finalize_goal(callback, state)


async def _finalize_goal(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    from app.database.session import AsyncSessionLocal
    from app.services.user_service import UserService
    from app.repositories.user import UserRepository

    async with AsyncSessionLocal() as session:
        user_service = UserService(session)
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(GOAL_USER_NOT_FOUND)
            return

        await user_service.set_goal(
            user_id=user.id,
            goal_type=data["goal_type"],
            intensity=data.get("intensity"),
        )
        targets = await user_service.get_today_targets(user.id)
        await session.commit()

    await callback.message.edit_text(  # type: ignore[union-attr]
        GOAL_SET_TEXT.format(
            goal_label=GOAL_LABELS.get(data["goal_type"], data["goal_type"]),
            calories=float(targets.calories),
            protein=float(targets.protein_g),
            fat=float(targets.fat_g),
            carbs=float(targets.carbs_g),
        ),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer(GOAL_SET_ANSWER)

    await callback.message.answer(GOAL_MENU_HINT, reply_markup=main_reply_keyboard())  # type: ignore[union-attr]
