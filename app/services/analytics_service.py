import uuid
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.food_log import FoodLog
from app.models.daily_targets import DailyTargets
from app.repositories.weight_history import WeightHistoryRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.weight_repo = WeightHistoryRepository(session)

    async def get_weekly_stats(self, user_id: uuid.UUID) -> dict:
        today = date.today()
        week_ago = today - timedelta(days=7)

        # Aggregate food logs for the past 7 days
        stmt = select(
            func.avg(FoodLog.total_calories).label("avg_calories"),
            func.avg(FoodLog.total_protein_g).label("avg_protein"),
            func.avg(FoodLog.total_fat_g).label("avg_fat"),
            func.avg(FoodLog.total_carbs_g).label("avg_carbs"),
            func.count(FoodLog.id).label("days_logged"),
        ).where(FoodLog.user_id == user_id, FoodLog.date >= week_ago, FoodLog.date <= today)

        result = await self.session.execute(stmt)
        row = result.first()

        # Get targets
        targets_stmt = select(DailyTargets).where(
            DailyTargets.user_id == user_id, DailyTargets.date == today
        )
        targets_result = await self.session.execute(targets_stmt)
        targets = targets_result.scalar_one_or_none()

        avg_calories = float(row.avg_calories or 0)
        avg_protein = float(row.avg_protein or 0)
        avg_fat = float(row.avg_fat or 0)
        avg_carbs = float(row.avg_carbs or 0)

        stats: dict = {
            "period": {"start": week_ago.isoformat(), "end": today.isoformat()},
            "days_logged": row.days_logged or 0,
            "averages": {
                "calories": round(avg_calories, 1),
                "protein_g": round(avg_protein, 1),
                "fat_g": round(avg_fat, 1),
                "carbs_g": round(avg_carbs, 1),
            },
            "targets": None,
            "adherence": None,
        }

        if targets:
            target_calories = float(targets.calories)
            target_protein = float(targets.protein_g)
            target_fat = float(targets.fat_g)
            target_carbs = float(targets.carbs_g)

            stats["targets"] = {
                "calories": target_calories,
                "protein_g": target_protein,
                "fat_g": target_fat,
                "carbs_g": target_carbs,
            }

            if target_calories > 0:
                calorie_pct = (avg_calories / target_calories) * 100
            else:
                calorie_pct = 0

            stats["adherence"] = {
                "calories_pct": round(calorie_pct, 1),
                "protein_pct": round((avg_protein / target_protein * 100) if target_protein else 0, 1),
                "fat_pct": round((avg_fat / target_fat * 100) if target_fat else 0, 1),
                "carbs_pct": round((avg_carbs / target_carbs * 100) if target_carbs else 0, 1),
            }

            # Identify problem areas
            issues = []
            if avg_protein < target_protein * 0.85:
                issues.append(f"Low protein: averaging {avg_protein:.0f}g vs {target_protein:.0f}g target")
            if avg_fat > target_fat * 1.15:
                issues.append(f"Excess fat: averaging {avg_fat:.0f}g vs {target_fat:.0f}g target")
            if avg_calories > target_calories * 1.1:
                issues.append(f"Over calories by {avg_calories - target_calories:.0f} kcal/day")
            elif avg_calories < target_calories * 0.8:
                issues.append(f"Under calories by {target_calories - avg_calories:.0f} kcal/day")
            stats["issues"] = issues

        return stats

    async def get_daily_breakdown(self, user_id: uuid.UUID, days: int = 7) -> list[dict]:
        today = date.today()
        start = today - timedelta(days=days - 1)

        stmt = (
            select(FoodLog)
            .where(FoodLog.user_id == user_id, FoodLog.date >= start)
            .order_by(FoodLog.date)
        )
        result = await self.session.execute(stmt)
        logs = result.scalars().all()

        return [
            {
                "date": log.date.isoformat(),
                "calories": float(log.total_calories),
                "protein_g": float(log.total_protein_g),
                "fat_g": float(log.total_fat_g),
                "carbs_g": float(log.total_carbs_g),
            }
            for log in logs
        ]
