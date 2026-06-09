import asyncio
from datetime import date, timedelta
from app.workers.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.cleanup.cleanup_old_data", bind=True)
def cleanup_old_data(self) -> dict:
    return asyncio.run(_cleanup_async())


async def _cleanup_async() -> dict:
    from sqlalchemy import delete
    from app.database.session import AsyncSessionLocal
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification

    cutoff = date.today() - timedelta(days=90)
    deleted = 0

    async with AsyncSessionLocal() as session:
        # Delete old sent notifications (keep 90 days)
        result = await session.execute(
            delete(Notification).where(
                Notification.is_sent == True,
                Notification.created_at < cutoff,  # type: ignore[operator]
            )
        )
        deleted += result.rowcount

        # Delete old audit logs (keep 90 days)
        result = await session.execute(
            delete(AuditLog).where(AuditLog.created_at < cutoff)  # type: ignore[operator]
        )
        deleted += result.rowcount

        await session.commit()

    logger.info("Cleanup completed", deleted_rows=deleted)
    return {"deleted": deleted}
