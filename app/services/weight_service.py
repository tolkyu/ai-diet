import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.weight_history import WeightHistory
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.weight_history import WeightHistoryRepository


class WeightService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.weight_repo = WeightHistoryRepository(session)

    async def log_weight(
        self,
        user_id: uuid.UUID,
        weight_kg: float,
        body_fat_pct: float | None = None,
        notes: str | None = None,
    ) -> WeightHistory:
        entry = await self.weight_repo.create(
            user_id=user_id,
            weight_kg=weight_kg,
            body_fat_pct=body_fat_pct,
            notes=notes,
        )
        # Update user's current weight
        user = await self.user_repo.get_or_raise(user_id)
        await self.user_repo.update(user, weight_kg=weight_kg)
        return entry

    async def get_trend(self, user_id: uuid.UUID, days: int = 30) -> dict:
        history = await self.weight_repo.get_history(user_id, limit=days)
        if not history:
            return {"entries": [], "change_kg": 0, "trend": "no_data"}

        weights = [float(h.weight_kg) for h in reversed(history)]
        dates = [h.measured_at.date().isoformat() for h in reversed(history)]

        change = weights[-1] - weights[0] if len(weights) > 1 else 0

        if len(weights) >= 3:
            # Simple linear regression slope
            n = len(weights)
            xs = list(range(n))
            slope = (n * sum(x * y for x, y in zip(xs, weights)) - sum(xs) * sum(weights)) / (
                n * sum(x ** 2 for x in xs) - sum(xs) ** 2
            )
            trend = "losing" if slope < -0.05 else "gaining" if slope > 0.05 else "stable"
        else:
            trend = "insufficient_data"

        return {
            "entries": [
                {"date": d, "weight_kg": w} for d, w in zip(dates, weights)
            ],
            "current_weight": weights[-1],
            "starting_weight": weights[0],
            "change_kg": round(change, 1),
            "trend": trend,
            "num_entries": len(weights),
        }
