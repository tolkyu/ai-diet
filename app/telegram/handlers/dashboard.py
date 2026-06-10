from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from app.core.constants import BAR_EMPTY, BAR_FILLED, PROGRESS_BAR_LENGTH
from app.core.logging import get_logger
from app.i18n.ua import (
    DASHBOARD_TITLE, DASHBOARD_CALORIES, DASHBOARD_PROTEIN, DASHBOARD_FAT,
    DASHBOARD_CARBS, DASHBOARD_CAL_ROW, DASHBOARD_MACRO_ROW,
    DASHBOARD_TIP_NOTHING, DASHBOARD_TIP_PROTEIN, DASHBOARD_TIP_CLOSE,
    DASHBOARD_TIP_OVER, DASHBOARD_NO_PROFILE, DASHBOARD_NO_GOAL, BTN_DASHBOARD,
    DASHBOARD_GOAL_PROGRESS, DASHBOARD_WATER, DASHBOARD_UPGRADE_TIP,
)

router = Router(name="dashboard")
logger = get_logger(__name__)

MONTHS_UA = [
    "", "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]


def _progress_bar(current: float, target: float, length: int = PROGRESS_BAR_LENGTH) -> str:
    if target <= 0:
        return BAR_EMPTY * length
    pct = min(current / target, 1.0)
    filled = round(pct * length)
    return BAR_FILLED * filled + BAR_EMPTY * (length - filled)


async def _build_dashboard_text(
    user,
    targets,
    food_log,
    goal=None,
    water_log=None,
    is_premium: bool = False,
) -> str:
    from datetime import date
    today = date.today()
    date_str = f"{today.day} {MONTHS_UA[today.month]}"

    cal_target   = float(targets.calories)
    prot_target  = float(targets.protein_g)
    fat_target   = float(targets.fat_g)
    carbs_target = float(targets.carbs_g)

    if food_log:
        cal_consumed   = float(food_log.total_calories)
        prot_consumed  = float(food_log.total_protein_g)
        fat_consumed   = float(food_log.total_fat_g)
        carbs_consumed = float(food_log.total_carbs_g)
    else:
        cal_consumed = prot_consumed = fat_consumed = carbs_consumed = 0.0

    cal_remaining  = max(cal_target - cal_consumed, 0)
    prot_remaining = max(prot_target - prot_consumed, 0)

    lines = [
        DASHBOARD_TITLE.format(date=date_str),
        "",
        f"{DASHBOARD_CALORIES}   {_progress_bar(cal_consumed, cal_target)}",
        f"   {DASHBOARD_CAL_ROW.format(consumed=cal_consumed, target=cal_target, remaining=cal_remaining)}",
        "",
        f"{DASHBOARD_PROTEIN}    {_progress_bar(prot_consumed, prot_target)}",
        f"   {DASHBOARD_MACRO_ROW.format(consumed=prot_consumed, target=prot_target, remaining=prot_remaining)}",
        "",
        f"{DASHBOARD_FAT}        {_progress_bar(fat_consumed, fat_target)}",
        f"   {fat_consumed:.0f} / {fat_target:.0f} г",
        "",
        f"{DASHBOARD_CARBS}  {_progress_bar(carbs_consumed, carbs_target)}",
        f"   {carbs_consumed:.0f} / {carbs_target:.0f} г",
    ]

    if cal_consumed == 0:
        lines += ["", DASHBOARD_TIP_NOTHING]
    elif prot_remaining > 30:
        lines += ["", DASHBOARD_TIP_PROTEIN.format(remaining=prot_remaining)]
    elif 0 < cal_remaining < 200:
        lines += ["", DASHBOARD_TIP_CLOSE]
    elif cal_consumed > cal_target:
        lines += ["", DASHBOARD_TIP_OVER.format(over=cal_consumed - cal_target)]

    # Premium: goal progress
    if is_premium and goal and goal.target_weight_kg and user.weight_kg:
        current_w = float(user.weight_kg)
        target_w  = float(goal.target_weight_kg)
        remaining = abs(target_w - current_w)

        if remaining > 0.1:
            # estimate days: use calorie delta relative to goal
            from app.core.constants import GoalType, CALORIE_ADJUSTMENTS
            intensity = goal.intensity
            daily_delta = 0
            if intensity:
                from app.core.constants import GoalIntensity
                try:
                    daily_delta = abs(CALORIE_ADJUSTMENTS.get(GoalIntensity(intensity), 500))
                except Exception:
                    daily_delta = 500
            if daily_delta == 0:
                daily_delta = 500
            # 1 kg ≈ 7700 kcal
            days_est = int((remaining * 7700) / daily_delta)
            lines.append(DASHBOARD_GOAL_PROGRESS.format(
                current=current_w, target=target_w,
                remaining=remaining, days=days_est,
            ))

    # Premium: water tracking
    if is_premium and water_log is not None:
        bar = _progress_bar(water_log.total_ml, water_log.goal_ml, length=8)
        lines.append(DASHBOARD_WATER.format(
            current=water_log.total_ml, goal=water_log.goal_ml, bar=bar
        ))
    elif not is_premium:
        lines.append(DASHBOARD_UPGRADE_TIP)

    return "\n".join(lines)


async def _get_dashboard_data(telegram_id: int):
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.food_log_service import FoodLogService
    from app.services.subscription_service import SubscriptionService
    from app.services.water_service import WaterService

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user_svc  = UserService(session)
        flog_svc  = FoodLogService(session)
        sub_svc   = SubscriptionService(session)

        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.is_registered:
            return None, None, None, None, None, False

        try:
            targets = await user_svc.get_today_targets(user.id)
        except Exception:
            return user, None, None, None, None, False

        food_log = await flog_svc.get_today_log(user.id)
        goal     = await user_svc.get_active_goal(user.id)
        sub_info = await sub_svc.get_usage_info(user.id, telegram_id=telegram_id)
        is_premium = sub_info["plan"] == "premium"

        water_log = None
        if is_premium:
            water_svc = WaterService(session)
            water_log = await water_svc.get_today_log(user.id)

        await session.commit()

    return user, targets, food_log, goal, water_log, is_premium


@router.message(Command("dashboard"))
@router.message(F.text == BTN_DASHBOARD)
async def cmd_dashboard(message: Message, state: FSMContext = None, user_service=None, food_log_service=None) -> None:  # type: ignore[assignment]
    from app.telegram.keyboards.inline import main_menu_keyboard

    if state:
        await state.clear()

    try:
        user, targets, food_log, goal, water_log, is_premium = await _get_dashboard_data(
            message.from_user.id  # type: ignore[union-attr]
        )
    except Exception as e:
        logger.error("Dashboard data fetch failed", error=str(e))
        await message.answer("Помилка при завантаженні дашборду. Спробуй ще раз.")
        return
    if not user:
        await message.answer(DASHBOARD_NO_PROFILE)
        return
    if targets is None:
        await message.answer(DASHBOARD_NO_GOAL)
        return

    text = await _build_dashboard_text(user, targets, food_log, goal, water_log, is_premium)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:dashboard")
async def menu_dashboard(callback: CallbackQuery) -> None:
    from app.telegram.keyboards.inline import main_menu_keyboard

    user, targets, food_log, goal, water_log, is_premium = await _get_dashboard_data(
        callback.from_user.id
    )
    if not user or targets is None:
        await callback.answer(DASHBOARD_NO_PROFILE)
        return

    text = await _build_dashboard_text(user, targets, food_log, goal, water_log, is_premium)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()
