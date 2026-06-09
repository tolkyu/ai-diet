import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import UserNotFoundError, UserNotRegisteredError, GoalNotFoundError
from app.models.user import User
from app.models.goal import Goal
from app.models.daily_targets import DailyTargets
from app.repositories.user import UserRepository
from app.repositories.subscription import SubscriptionRepository
from app.services.nutrition_service import NutritionService
from app.core.constants import GoalType


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.sub_repo = SubscriptionRepository(session)
        self.nutrition = NutritionService()

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        user, created = await self.user_repo.get_or_create_by_telegram_id(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        if created:
            await self.sub_repo.create(user_id=user.id)
        return user, created

    async def complete_registration(
        self,
        telegram_id: int,
        gender: str,
        age: int,
        height_cm: float,
        weight_kg: float,
        activity_level: str,
    ) -> User:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if not user:
            raise UserNotFoundError(telegram_id)

        user = await self.user_repo.update(
            user,
            gender=gender,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            is_registered=True,
        )
        return user

    async def set_goal(
        self,
        user_id: uuid.UUID,
        goal_type: str,
        intensity: str | None = None,
        target_weight_kg: float | None = None,
    ) -> Goal:
        # Deactivate existing active goals
        from sqlalchemy import select, update
        stmt = (
            select(Goal)
            .where(Goal.user_id == user_id, Goal.is_active == True)
        )
        result = await self.session.execute(stmt)
        for old_goal in result.scalars().all():
            old_goal.is_active = False
            self.session.add(old_goal)
        await self.session.flush()

        goal = Goal(
            user_id=user_id,
            goal_type=goal_type,
            intensity=intensity,
            target_weight_kg=target_weight_kg,
            is_active=True,
        )
        self.session.add(goal)
        await self.session.flush()
        await self.session.refresh(goal)

        # Calculate and store today's targets
        await self.refresh_daily_targets(user_id, goal)
        return goal

    async def get_active_goal(self, user_id: uuid.UUID) -> Goal | None:
        from sqlalchemy import select
        stmt = select(Goal).where(Goal.user_id == user_id, Goal.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def refresh_daily_targets(
        self, user_id: uuid.UUID, goal: Goal | None = None
    ) -> DailyTargets:
        from sqlalchemy import select
        user = await self.user_repo.get_or_raise(user_id)

        if goal is None:
            goal = await self.get_active_goal(user_id)
        if goal is None:
            raise GoalNotFoundError()

        targets = self.nutrition.calculate_targets(
            gender=user.gender,
            weight_kg=float(user.weight_kg),  # type: ignore[arg-type]
            height_cm=float(user.height_cm),  # type: ignore[arg-type]
            age=user.age,  # type: ignore[arg-type]
            activity_level=user.activity_level,
            goal_type=goal.goal_type,
            intensity=goal.intensity,
        )

        today = date.today()
        stmt = select(DailyTargets).where(
            DailyTargets.user_id == user_id, DailyTargets.date == today
        )
        result = await self.session.execute(stmt)
        daily = result.scalar_one_or_none()

        if daily:
            daily.bmr = targets.bmr
            daily.tdee = targets.tdee
            daily.calories = targets.calories
            daily.protein_g = targets.protein_g
            daily.fat_g = targets.fat_g
            daily.carbs_g = targets.carbs_g
        else:
            daily = DailyTargets(
                user_id=user_id,
                date=today,
                bmr=targets.bmr,
                tdee=targets.tdee,
                calories=targets.calories,
                protein_g=targets.protein_g,
                fat_g=targets.fat_g,
                carbs_g=targets.carbs_g,
            )
        self.session.add(daily)
        await self.session.flush()
        await self.session.refresh(daily)
        return daily

    async def get_today_targets(self, user_id: uuid.UUID) -> DailyTargets:
        from sqlalchemy import select
        today = date.today()
        stmt = select(DailyTargets).where(
            DailyTargets.user_id == user_id, DailyTargets.date == today
        )
        result = await self.session.execute(stmt)
        daily = result.scalar_one_or_none()
        if daily:
            return daily
        return await self.refresh_daily_targets(user_id)
