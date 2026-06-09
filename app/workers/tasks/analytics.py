import asyncio
from app.workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.analytics.generate_weekly_reports", bind=True)
def generate_weekly_reports(self) -> dict:
    return asyncio.run(_generate_weekly_reports_async())


async def _generate_weekly_reports_async() -> dict:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.analytics_service import AnalyticsService
    from app.services.user_service import UserService
    from app.ai.coach import ai_coach
    from app.telegram.bot import bot

    sent = 0
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_registered_active()

        for user in users:
            try:
                analytics_svc = AnalyticsService(session)
                user_svc = UserService(session)

                stats = await analytics_svc.get_weekly_stats(user.id)
                if stats["days_logged"] < 3:
                    continue

                goal = await user_svc.get_active_goal(user.id)
                if not goal:
                    continue

                targets = stats.get("targets") or {}
                issues = "; ".join(stats.get("issues", [])) or "None"

                summary = await ai_coach.generate_weekly_summary({
                    "user_id": user.id,
                    "name": user.display_name,
                    "goal_type": goal.goal_type,
                    "intensity": goal.intensity or "maintain",
                    "calorie_target": targets.get("calories", 0),
                    "avg_calories": stats["averages"]["calories"],
                    "avg_protein": stats["averages"]["protein_g"],
                    "avg_fat": stats["averages"]["fat_g"],
                    "avg_carbs": stats["averages"]["carbs_g"],
                    "days_logged": stats["days_logged"],
                    "weight_change": 0,
                    "issues": issues,
                }, session=session)

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"📊 <b>Your Weekly Report</b>\n\n{summary}",
                    parse_mode="HTML",
                )
                sent += 1
            except Exception as e:
                logger.error("Weekly report failed", telegram_id=user.telegram_id, error=str(e))

        await session.commit()

    logger.info("Weekly reports sent", count=sent)
    return {"sent": sent}
