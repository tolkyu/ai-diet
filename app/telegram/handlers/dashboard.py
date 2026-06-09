from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.core.constants import BAR_EMPTY, BAR_FILLED, PROGRESS_BAR_LENGTH
from app.core.logging import get_logger
from app.i18n.ua import (
    DASHBOARD_TITLE, DASHBOARD_CALORIES, DASHBOARD_PROTEIN, DASHBOARD_FAT,
    DASHBOARD_CARBS, DASHBOARD_CAL_ROW, DASHBOARD_MACRO_ROW,
    DASHBOARD_TIP_NOTHING, DASHBOARD_TIP_PROTEIN, DASHBOARD_TIP_CLOSE,
    DASHBOARD_TIP_OVER, DASHBOARD_NO_PROFILE, DASHBOARD_NO_GOAL, BTN_DASHBOARD,
)

router = Router(name="dashboard")
logger = get_logger(__name__)


def _progress_bar(current: float, target: float) -> str:
    if target <= 0:
        return BAR_EMPTY * PROGRESS_BAR_LENGTH
    pct = min(current / target, 1.0)
    filled = round(pct * PROGRESS_BAR_LENGTH)
    return BAR_FILLED * filled + BAR_EMPTY * (PROGRESS_BAR_LENGTH - filled)


def _build_dashboard_text(user_name: str, targets, food_log) -> str:
    from datetime import date
    import locale
    MONTHS_UA = [
        "", "січня", "лютого", "березня", "квітня", "травня", "червня",
        "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
    ]
    today = date.today()
    date_str = f"{today.day} {MONTHS_UA[today.month]}"

    cal_target  = float(targets.calories)
    prot_target = float(targets.protein_g)
    fat_target  = float(targets.fat_g)
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

    return "\n".join(lines)


@router.message(Command("dashboard"))
@router.message(F.text == BTN_DASHBOARD)
async def cmd_dashboard(message: Message, user_service, food_log_service) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.food_log_service import FoodLogService
    from app.telegram.keyboards.inline import main_menu_keyboard

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user_svc  = UserService(session)
        flog_svc  = FoodLogService(session)

        user = await user_repo.get_by_telegram_id(message.from_user.id)  # type: ignore[union-attr]
        if not user or not user.is_registered:
            await message.answer(DASHBOARD_NO_PROFILE)
            return

        try:
            targets = await user_svc.get_today_targets(user.id)
        except Exception:
            await message.answer(DASHBOARD_NO_GOAL)
            return

        food_log = await flog_svc.get_today_log(user.id)
        await session.commit()

    text = _build_dashboard_text(user.display_name, targets, food_log)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu:dashboard")
async def menu_dashboard(callback: CallbackQuery) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.food_log_service import FoodLogService
    from app.telegram.keyboards.inline import main_menu_keyboard

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user_svc  = UserService(session)
        flog_svc  = FoodLogService(session)

        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user or not user.is_registered:
            await callback.answer(DASHBOARD_NO_PROFILE)
            return

        targets  = await user_svc.get_today_targets(user.id)
        food_log = await flog_svc.get_today_log(user.id)
        await session.commit()

    text = _build_dashboard_text(user.display_name, targets, food_log)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()
