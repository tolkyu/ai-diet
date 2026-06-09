from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from app.core.constants import BAR_EMPTY, BAR_FILLED, PROGRESS_BAR_LENGTH
from app.core.logging import get_logger
from app.i18n.ua import (
    STATS_GENERATING, STATS_TITLE, STATS_DAYS_LOGGED, STATS_AVERAGES,
    STATS_CALORIES_AVG, STATS_PROTEIN_AVG, STATS_FAT_AVG, STATS_CARBS_AVG,
    STATS_ADHERENCE, STATS_ISSUES, STATS_AI_SUMMARY, STATS_NO_PROFILE,
    STATS_CAL_ADHERENCE, STATS_PROT_ADHERENCE, STATS_FAT_ADHERENCE,
    STATS_CARBS_ADHERENCE, BTN_STATS,
)

router = Router(name="stats")
logger = get_logger(__name__)


def _progress_bar(pct: float) -> str:
    pct = min(pct / 100, 1.0)
    filled = round(pct * PROGRESS_BAR_LENGTH)
    return BAR_FILLED * filled + BAR_EMPTY * (PROGRESS_BAR_LENGTH - filled)


def _build_stats_text(stats: dict, ai_summary: str | None = None) -> str:
    avgs      = stats["averages"]
    targets   = stats.get("targets")
    adherence = stats.get("adherence")
    days      = stats["days_logged"]

    lines = [
        STATS_TITLE,
        f"<i>{stats['period']['start']} → {stats['period']['end']}</i>",
        STATS_DAYS_LOGGED.format(days=days),
        "",
        STATS_AVERAGES,
        STATS_CALORIES_AVG.format(val=avgs["calories"]),
        STATS_PROTEIN_AVG.format(val=avgs["protein_g"]),
        STATS_FAT_AVG.format(val=avgs["fat_g"]),
        STATS_CARBS_AVG.format(val=avgs["carbs_g"]),
    ]

    if targets and adherence:
        lines += [
            "",
            STATS_ADHERENCE,
            STATS_CAL_ADHERENCE.format(bar=_progress_bar(adherence["calories_pct"]), pct=adherence["calories_pct"]),
            STATS_PROT_ADHERENCE.format(bar=_progress_bar(adherence["protein_pct"]),  pct=adherence["protein_pct"]),
            STATS_FAT_ADHERENCE.format(bar=_progress_bar(adherence["fat_pct"]),       pct=adherence["fat_pct"]),
            STATS_CARBS_ADHERENCE.format(bar=_progress_bar(adherence["carbs_pct"]),   pct=adherence["carbs_pct"]),
        ]

    issues = stats.get("issues", [])
    if issues:
        lines += [STATS_ISSUES]
        for issue in issues:
            lines.append(f"• {issue}")

    if ai_summary:
        lines += [STATS_AI_SUMMARY, f"<i>{ai_summary}</i>"]

    return "\n".join(lines)


@router.message(Command("stats"))
@router.message(F.text == BTN_STATS)
@router.callback_query(F.data == "menu:stats")
async def cmd_stats(event: Message | CallbackQuery) -> None:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.analytics_service import AnalyticsService
    from app.services.user_service import UserService
    from app.ai.coach import ai_coach
    from app.telegram.keyboards.inline import main_menu_keyboard

    telegram_id = event.from_user.id  # type: ignore[union-attr]

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(STATS_GENERATING)  # type: ignore[union-attr]
    else:
        await event.answer(STATS_GENERATING)

    async with AsyncSessionLocal() as session:
        user_repo     = UserRepository(session)
        analytics_svc = AnalyticsService(session)
        user_svc      = UserService(session)

        user = await user_repo.get_by_telegram_id(telegram_id)
        if not user or not user.is_registered:
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(STATS_NO_PROFILE)  # type: ignore[union-attr]
            else:
                await event.answer(STATS_NO_PROFILE)
            return

        stats = await analytics_svc.get_weekly_stats(user.id)
        goal  = await user_svc.get_active_goal(user.id)
        await session.commit()

    ai_summary = None
    if stats["days_logged"] >= 3 and goal:
        try:
            issues_str = "; ".join(stats.get("issues", [])) or "None identified"
            tgt = stats.get("targets", {}) or {}
            ai_summary = await ai_coach.generate_weekly_summary({
                "name":           user.display_name,
                "goal_type":      goal.goal_type,
                "intensity":      goal.intensity or "none",
                "calorie_target": tgt.get("calories", 0),
                "avg_calories":   stats["averages"]["calories"],
                "avg_protein":    stats["averages"]["protein_g"],
                "avg_fat":        stats["averages"]["fat_g"],
                "avg_carbs":      stats["averages"]["carbs_g"],
                "days_logged":    stats["days_logged"],
                "weight_change":  0,
                "issues":         issues_str,
            })
        except Exception as e:
            logger.warning("AI summary failed", error=str(e))

    text = _build_stats_text(stats, ai_summary)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=main_menu_keyboard())
