from datetime import datetime, timezone, timedelta
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select
from app.core.config import settings
from app.core.logging import get_logger
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.user import User

router = Router(name="admin")
logger = get_logger(__name__)

_STARS_TO_USD = 0.013  # 1 Star ≈ $0.013


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in settings.admin_telegram_ids_set


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id):  # type: ignore[union-attr]
        return

    from app.database.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        total_users = (await session.execute(
            select(func.count(User.id)).where(User.is_registered == True)  # noqa: E712
        )).scalar() or 0

        total_all_users = (await session.execute(
            select(func.count(User.id))
        )).scalar() or 0

        active_premium = (await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.plan == "premium",
                Subscription.status == "active",
            )
        )).scalar() or 0

        total_stars = (await session.execute(
            select(func.sum(Payment.stars_amount)).where(Payment.status == "succeeded")
        )).scalar() or 0

        week_result = (await session.execute(
            select(
                func.count(Payment.id).label("cnt"),
                func.sum(Payment.stars_amount).label("stars"),
            ).where(
                Payment.status == "succeeded",
                Payment.created_at >= week_ago,
            )
        )).first()
        week_count = week_result.cnt if week_result else 0
        week_stars = week_result.stars if week_result else 0

        recent_rows = (await session.execute(
            select(Payment, User)
            .join(User, Payment.user_id == User.id)
            .where(Payment.status == "succeeded")
            .order_by(Payment.created_at.desc())
            .limit(7)
        )).all()

    usd_total = float(total_stars) * _STARS_TO_USD
    usd_week  = float(week_stars or 0) * _STARS_TO_USD

    plan_labels = {"monthly": "1 міс", "yearly": "1 рік"}

    lines = [
        "🛡 <b>Адмін-панель</b>",
        "",
        f"👥 Користувачів: <b>{total_users}</b> зареєстровано · {total_all_users} всього",
        f"⭐ Активних преміум: <b>{active_premium}</b>",
        "",
        "💰 <b>Дохід:</b>",
        f"• Всього: <b>{total_stars} ⭐</b>  (~${usd_total:.1f})",
        f"• За 7 днів: <b>{week_stars or 0} ⭐</b>  (~${usd_week:.1f})  [{week_count} платежів]",
        "",
        "🕐 <b>Останні платежі:</b>",
    ]

    if not recent_rows:
        lines.append("  — платежів ще немає")
    else:
        for payment, user in recent_rows:
            name = f"@{user.username}" if user.username else user.first_name or str(user.telegram_id)
            plan = plan_labels.get(payment.plan, payment.plan)
            date = payment.created_at.strftime("%d.%m") if payment.created_at else "?"
            lines.append(f"• {name} · {payment.stars_amount} ⭐ · {plan} · {date}")

    await message.answer("\n".join(lines), parse_mode="HTML")
    logger.info("Admin panel viewed", admin_id=message.from_user.id)  # type: ignore[union-attr]
