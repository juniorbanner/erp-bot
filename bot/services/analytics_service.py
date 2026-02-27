import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from db.models.transaction import Transaction, TransactionType
from db.models.order import Order, OrderStatus, PaymentType
from db.models.user import User


async def get_daily_report(session: AsyncSession, date: datetime.date | None = None) -> dict:
    if date is None:
        date = datetime.date.today()

    tz = datetime.timezone(datetime.timedelta(hours=5))  # UTC+5 Uzbekistan
    start = datetime.datetime.combine(date, datetime.time.min, tzinfo=tz)
    end = datetime.datetime.combine(date, datetime.time.max, tzinfo=tz)

    # Cash revenue from delivered orders
    cash_result = await session.execute(
        select(func.coalesce(func.sum(Order.total_amount), 0)).where(
            and_(
                Order.created_at.between(start, end),
                Order.payment_type == PaymentType.CASH,
                Order.status == OrderStatus.DELIVERED,
            )
        )
    )
    cash_revenue = float(cash_result.scalar())

    # New debts added today
    debt_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.created_at.between(start, end),
                Transaction.type == TransactionType.DEBT_ADDED,
            )
        )
    )
    new_debt = float(debt_result.scalar())

    # Repayments today
    repay_result = await session.execute(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            and_(
                Transaction.created_at.between(start, end),
                Transaction.type == TransactionType.DEBT_REPAID,
            )
        )
    )
    repayments = abs(float(repay_result.scalar()))

    # Total active debtors count
    debtors_count = await session.scalar(
        select(func.count(User.id)).where(User.nasiya_balance > 0)
    )

    # Top 5 debtors
    top_debtors_result = await session.execute(
        select(User)
        .where(User.nasiya_balance > 0)
        .order_by(User.nasiya_balance.desc())
        .limit(5)
    )
    top_debtors = list(top_debtors_result.scalars().all())

    return {
        "date": date,
        "cash_revenue": cash_revenue,
        "new_debt": new_debt,
        "repayments": repayments,
        "debtors_count": debtors_count or 0,
        "top_debtors": top_debtors,
    }
