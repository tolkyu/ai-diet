from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_by_telegram_id(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        user = await self.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        return user, True

    async def get_all_registered_active(self) -> list[User]:
        stmt = select(User).where(User.is_registered == True, User.is_active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
