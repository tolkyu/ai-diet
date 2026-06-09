"""
Celery tasks for proactive coaching notifications.

Uses asyncio.run() because Celery workers are synchronous;
each task creates its own async context.
"""
import asyncio
from datetime import date
from app.workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.notifications.send_morning_coaching", bind=True)
def send_morning_coaching(self) -> dict:
    return asyncio.run(_send_morning_coaching_async())


async def _send_morning_coaching_async() -> dict:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.food_log_service import FoodLogService
    from app.repositories.weight_history import WeightHistoryRepository
    from app.ai.coach import ai_coach
    from app.telegram.bot import bot

    sent = 0
    failed = 0

    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_registered_active()

        for user in users:
            try:
                user_svc = UserService(session)
                flog_svc = FoodLogService(session)
                weight_repo = WeightHistoryRepository(session)
                goal = await user_svc.get_active_goal(user.id)
                if not goal:
                    continue

                targets = await user_svc.get_today_targets(user.id)
                yesterday = date.today().replace(day=date.today().day - 1) if date.today().day > 1 else date.today()
                yesterday_log = await flog_svc.get_today_log(user.id)
                latest_weight = await weight_repo.get_latest(user.id)

                message = await ai_coach.generate_morning_message(
                    user_data={
                        "user_id": user.id,
                        "name": user.display_name,
                        "goal_type": goal.goal_type,
                        "intensity": goal.intensity or "none",
                        "calories": float(targets.calories),
                        "protein_g": float(targets.protein_g),
                        "fat_g": float(targets.fat_g),
                        "carbs_g": float(targets.carbs_g),
                        "weight_kg": float(user.weight_kg) if user.weight_kg else 0,
                        "days_tracking": 1,
                        "yesterday_calories": float(yesterday_log.total_calories) if yesterday_log else 0,
                        "yesterday_protein": float(yesterday_log.total_protein_g) if yesterday_log else 0,
                    },
                    session=session,
                )

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"🌅 Good morning, {user.display_name}!\n\n{message}",
                )
                sent += 1
            except Exception as e:
                logger.error(
                    "Failed to send morning coaching",
                    telegram_id=user.telegram_id,
                    error=str(e),
                )
                failed += 1

        await session.commit()

    logger.info("Morning coaching sent", sent=sent, failed=failed)
    return {"sent": sent, "failed": failed}


@celery_app.task(name="app.workers.tasks.notifications.send_evening_check", bind=True)
def send_evening_check(self) -> dict:
    return asyncio.run(_send_evening_check_async())


async def _send_evening_check_async() -> dict:
    from app.database.session import AsyncSessionLocal
    from app.repositories.user import UserRepository
    from app.services.user_service import UserService
    from app.services.food_log_service import FoodLogService
    from app.ai.coach import ai_coach
    from app.telegram.bot import bot

    sent = 0
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all_registered_active()

        for user in users:
            try:
                user_svc = UserService(session)
                flog_svc = FoodLogService(session)
                goal = await user_svc.get_active_goal(user.id)
                if not goal:
                    continue

                targets = await user_svc.get_today_targets(user.id)
                today_log = await flog_svc.get_today_log(user.id)

                consumed_cal = float(today_log.total_calories) if today_log else 0
                consumed_prot = float(today_log.total_protein_g) if today_log else 0

                message = await ai_coach.generate_evening_check(
                    user_data={
                        "user_id": user.id,
                        "name": user.display_name,
                        "goal_type": goal.goal_type,
                        "calories": float(targets.calories),
                        "protein_g": float(targets.protein_g),
                        "consumed_calories": consumed_cal,
                        "consumed_protein": consumed_prot,
                        "remaining_calories": max(float(targets.calories) - consumed_cal, 0),
                        "remaining_protein": max(float(targets.protein_g) - consumed_prot, 0),
                    },
                    session=session,
                )

                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"🌆 Evening check-in!\n\n{message}",
                )
                sent += 1
            except Exception as e:
                logger.error("Evening check failed", telegram_id=user.telegram_id, error=str(e))

        await session.commit()

    return {"sent": sent}
