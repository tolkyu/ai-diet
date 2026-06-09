import time
from fastapi import APIRouter
from sqlalchemy import text
from app.database.session import AsyncSessionLocal
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
_start_time = time.time()


@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "env": settings.app_env}


@router.get("/health/detailed")
async def detailed_health() -> dict:
    checks: dict = {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
        "components": {},
    }

    # Database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["components"]["database"] = {"status": "ok"}
    except Exception as e:
        checks["components"]["database"] = {"status": "error", "detail": str(e)}
        checks["status"] = "degraded"

    # Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["components"]["redis"] = {"status": "ok"}
    except Exception as e:
        checks["components"]["redis"] = {"status": "error", "detail": str(e)}
        checks["status"] = "degraded"

    return checks
