from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.utils.formatters import fmt_uzs, fmt_date
from db.models.user import User
from db.models.order import Order, OrderStatus

router = Router()

STATUS_LABELS = {
    OrderStatus.PENDING: "⏳ Ожидает",
    OrderStatus.CONFIRMED: "✅ Подтверждён",
    OrderStatus.DELIVERED: "📦 Доставлен",
    OrderStatus.CANCELLED: "❌ Отменён",
}


@router.message(F.text == "📜 История покупок")
async def cmd_orders(message: Message, db_user: User, session: AsyncSession, **kwargs):
    result = await session.execute(
        select(Order)
        .where(Order.user_id == db_user.id)
        .order_by(Order.created_at.desc())
        .limit(10)
    )
    orders = list(result.scalars().all())

    if not orders:
        await message.answer("📜 История покупок пуста.")
        return

    text = "📜 <b>История покупок (последние 10)</b>\n\n"
    for order in orders:
        status = STATUS_LABELS.get(order.status, order.status)
        text += (
            f"🛒 Заказ #{order.id} — {fmt_date(order.created_at)}\n"
            f"   Сумма: {fmt_uzs(order.total_amount)} | {status}\n\n"
        )

    await message.answer(text, parse_mode="HTML")
