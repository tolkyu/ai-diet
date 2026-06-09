"""Integration tests for the complete user registration and goal-setting flow."""
import pytest
import pytest_asyncio
from decimal import Decimal


@pytest.mark.asyncio
class TestUserRegistrationFlow:
    async def test_create_user_from_telegram(self, db_session):
        from app.services.user_service import UserService

        svc = UserService(db_session)
        user, created = await svc.get_or_create_user(
            telegram_id=999001,
            username="testuser",
            first_name="Test",
        )

        assert created is True
        assert user.telegram_id == 999001
        assert user.username == "testuser"
        assert not user.is_registered

    async def test_second_get_returns_existing_user(self, db_session):
        from app.services.user_service import UserService

        svc = UserService(db_session)
        await svc.get_or_create_user(telegram_id=999002)
        _, created = await svc.get_or_create_user(telegram_id=999002)
        assert created is False

    async def test_complete_registration(self, db_session):
        from app.services.user_service import UserService

        svc = UserService(db_session)
        user, _ = await svc.get_or_create_user(telegram_id=999003, first_name="Jane")

        user = await svc.complete_registration(
            telegram_id=999003,
            gender="female",
            age=28,
            height_cm=162,
            weight_kg=58,
            activity_level="lightly_active",
        )

        assert user.is_registered
        assert user.gender == "female"
        assert user.age == 28
        assert float(user.height_cm) == 162.0

    async def test_full_registration_and_goal_flow(self, db_session):
        from app.services.user_service import UserService
        from app.services.nutrition_service import NutritionService

        svc = UserService(db_session)
        user, _ = await svc.get_or_create_user(telegram_id=999004, first_name="Mike")

        user = await svc.complete_registration(
            telegram_id=999004,
            gender="male",
            age=30,
            height_cm=180,
            weight_kg=85,
            activity_level="moderately_active",
        )

        goal = await svc.set_goal(
            user_id=user.id,
            goal_type="lose_weight",
            intensity="moderate",
        )

        assert goal.is_active
        assert goal.goal_type == "lose_weight"

        targets = await svc.get_today_targets(user.id)

        # Validate calculated targets are scientifically reasonable
        assert float(targets.bmr) > 1500  # typical male BMR
        assert float(targets.tdee) > float(targets.bmr)
        assert float(targets.calories) < float(targets.tdee)  # deficit applied
        assert float(targets.protein_g) > 100  # adequate protein
        assert float(targets.fat_g) > 30   # adequate fat
        assert float(targets.carbs_g) > 50  # minimum carbs

    async def test_subscription_created_on_user_creation(self, db_session):
        from app.services.user_service import UserService
        from app.repositories.subscription import SubscriptionRepository

        svc = UserService(db_session)
        user, _ = await svc.get_or_create_user(telegram_id=999005)

        sub_repo = SubscriptionRepository(db_session)
        sub = await sub_repo.get_by_user_id(user.id)

        assert sub is not None
        assert sub.plan == "free"
