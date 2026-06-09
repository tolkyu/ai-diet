import uuid
import pytest
import pytest_asyncio
from datetime import date
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestFoodLogService:
    async def test_get_today_log_returns_none_when_empty(self, db_session):
        from app.services.food_log_service import FoodLogService
        svc = FoodLogService(db_session)
        user_id = uuid.uuid4()
        result = await svc.get_today_log(user_id)
        assert result is None

    async def test_add_entries_creates_food_log(self, db_session):
        from app.services.food_log_service import FoodLogService
        from app.services.user_service import UserService
        from app.models.user import User

        # Create user first
        user = User(
            telegram_id=123456,
            gender="male",
            age=25,
            height_cm=175,
            weight_kg=75,
            activity_level="sedentary",
            is_registered=True,
        )
        db_session.add(user)
        await db_session.flush()

        svc = FoodLogService(db_session)
        entries_data = [
            {
                "name": "Chicken breast",
                "amount_g": 200,
                "calories": 330,
                "protein_g": 62,
                "fat_g": 7,
                "carbs_g": 0,
                "confidence_score": 0.95,
            }
        ]

        with patch.object(svc, "check_and_increment_quota", new_callable=AsyncMock):
            food_log, entries = await svc.add_food_entries(
                user_id=user.id,
                entries_data=entries_data,
                raw_input="200g chicken breast",
            )

        assert food_log is not None
        assert len(entries) == 1
        assert float(food_log.total_calories) == pytest.approx(330, abs=1)
        assert float(food_log.total_protein_g) == pytest.approx(62, abs=1)

    async def test_add_multiple_entries_accumulates_totals(self, db_session):
        from app.services.food_log_service import FoodLogService
        from app.models.user import User
        from unittest.mock import patch, AsyncMock

        user = User(
            telegram_id=654321, gender="female", age=30,
            height_cm=165, weight_kg=60, activity_level="lightly_active", is_registered=True
        )
        db_session.add(user)
        await db_session.flush()

        svc = FoodLogService(db_session)

        with patch.object(svc, "check_and_increment_quota", new_callable=AsyncMock):
            await svc.add_food_entries(
                user.id,
                [{"name": "Oats", "amount_g": 80, "calories": 300, "protein_g": 10, "fat_g": 5, "carbs_g": 55}],
            )
            food_log, _ = await svc.add_food_entries(
                user.id,
                [{"name": "Banana", "amount_g": 120, "calories": 107, "protein_g": 1.3, "fat_g": 0.4, "carbs_g": 27}],
            )

        assert float(food_log.total_calories) == pytest.approx(407, abs=1)
