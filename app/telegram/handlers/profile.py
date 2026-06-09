from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.telegram.keyboards.inline import main_menu_keyboard
from app.core.logging import get_logger
from app.i18n.ua import (
    PROFILE_TITLE, PROFILE_NOT_FOUND, PROFILE_GENDER_M, PROFILE_GENDER_F,
    PROFILE_GOAL_NOT_SET, ACTIVITY_LABELS_UA, GOAL_LABELS, BTN_PROFILE,
)

router = Router(name="profile")
logger = get_logger(__name__)


@router.message(Command("profile"))
@router.message(F.text == BTN_PROFILE)
@router.callback_query(F.data == "menu:profile")
async def cmd_profile(event: Message | CallbackQuery) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.subscription_service import SubscriptionService

    telegram_id = event.from_user.id  # type: ignore[union-attr]

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user_svc  = UserService(session)
        sub_svc   = SubscriptionService(session)

        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.is_registered:
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(PROFILE_NOT_FOUND)  # type: ignore[union-attr]
            else:
                await event.answer(PROFILE_NOT_FOUND)
            return

        goal     = await user_svc.get_active_goal(user.id)
        sub_info = await sub_svc.get_usage_info(user.id)

        targets_text = ""
        try:
            targets = await user_svc.get_today_targets(user.id)
            targets_text = (
                f"\n\n📋 <b>Денні норми:</b>\n"
                f"• Калорії: {float(targets.calories):.0f} ккал\n"
                f"• Білки: {float(targets.protein_g):.0f}г | "
                f"Жири: {float(targets.fat_g):.0f}г | "
                f"Вуглеводи: {float(targets.carbs_g):.0f}г"
            )
        except Exception:
            pass

        await session.commit()

    gender_text = PROFILE_GENDER_M if user.gender == "male" else PROFILE_GENDER_F
    activity_text = ACTIVITY_LABELS_UA.get(user.activity_level or "", user.activity_level or "—")

    if goal:
        goal_text = GOAL_LABELS.get(goal.goal_type, goal.goal_type)
        if goal.intensity:
            goal_text += f" ({goal.intensity})"
    else:
        goal_text = PROFILE_GOAL_NOT_SET

    plan_emoji = "⭐" if sub_info["plan"] == "premium" else "🆓"
    plan_name  = "Преміум" if sub_info["plan"] == "premium" else "Безкоштовний"

    text = (
        f"{PROFILE_TITLE}\n\n"
        f"Ім'я: {user.display_name}\n"
        f"Стать: {gender_text}\n"
        f"Вік: {user.age} р.\n"
        f"Зростання: {float(user.height_cm):.0f} см\n"
        f"Вага: {float(user.weight_kg):.1f} кг\n"
        f"Активність: {activity_text}\n"
        f"\n🎯 Ціль: {goal_text}"
        + targets_text +
        f"\n\n{plan_emoji} План: {plan_name}"
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
