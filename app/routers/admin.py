from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, select
from app.core.config import settings
from app.core.security import verify_api_key
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.food_log import FoodLog
from app.models.ai_analysis import AIAnalysis

router = APIRouter(prefix="/admin")


async def verify_admin(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or not verify_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/stats", dependencies=[Depends(verify_admin)])
async def admin_stats() -> dict:
    async with AsyncSessionLocal() as session:
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        registered = (
            await session.execute(
                select(func.count(User.id)).where(User.is_registered == True)
            )
        ).scalar_one()
        total_logs = (await session.execute(select(func.count(FoodLog.id)))).scalar_one()
        total_analyses = (
            await session.execute(select(func.count(AIAnalysis.id)))
        ).scalar_one()
        total_tokens = (
            await session.execute(select(func.sum(AIAnalysis.tokens_used)))
        ).scalar_one()

    return {
        "users": {"total": total_users, "registered": registered},
        "food_logs": total_logs,
        "ai_analyses": total_analyses,
        "total_tokens_used": total_tokens or 0,
    }


@router.get("/users", dependencies=[Depends(verify_admin)])
async def list_users(limit: int = 50, offset: int = 0) -> list[dict]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

    return [
        {
            "id": str(u.id),
            "telegram_id": u.telegram_id,
            "username": u.username,
            "name": u.display_name,
            "is_registered": u.is_registered,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]
