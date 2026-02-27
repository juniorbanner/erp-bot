from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from bot.config import settings
from bot.utils.formatters import fmt_uzs, fmt_date


async def send_debt_notification(
    bot: Bot,
    telegram_id: int,
    amount: float,
    new_balance: float,
    comment: str | None = None,
):
    sign = "+" if amount > 0 else ""
    emoji = "📈" if amount > 0 else "📉"
    text = (
        f"{emoji} <b>Обновление по nasiya</b>\n\n"
        f"Изменение: {sign}{fmt_uzs(amount)}\n"
        f"Текущий долг: <b>{fmt_uzs(new_balance)}</b>\n"
    )
    if comment:
        text += f"Комментарий: {comment}\n"
    text += "\nДля деталей: /balance"
    await _safe_send(bot, telegram_id, text)


async def send_order_receipt(bot: Bot, telegram_id: int, order):
    from db.models.order import PaymentType
    payment_labels = {
        PaymentType.CASH: "💵 Наличные",
        PaymentType.NASIYA: "📒 Nasiya (в долг)",
        PaymentType.CARD: "💳 Карта",
    }
    items_text = ""
    for item in order.items:
        items_text += f"  • {item.product.name} × {item.quantity} = {fmt_uzs(item.unit_price * item.quantity)}\n"

    text = (
        f"🧾 <b>Чек заказа #{order.id}</b>\n\n"
        f"{items_text}\n"
        f"💰 Итого: <b>{fmt_uzs(order.total_amount)}</b>\n"
        f"Оплата: {payment_labels.get(order.payment_type, '—')}\n"
        f"Дата: {fmt_date(order.created_at)}\n"
    )
    await _safe_send(bot, telegram_id, text)


async def send_debt_reminder(bot: Bot, telegram_id: int, balance: float, client_name: str):
    text = (
        f"⏰ <b>Напоминание о задолженности</b>\n\n"
        f"Уважаемый(ая) {client_name},\n"
        f"Ваш текущий долг: <b>{fmt_uzs(balance)}</b>\n\n"
        "Пожалуйста, погасите задолженность при следующем визите.\n"
        "Проверить детали: /balance"
    )
    await _safe_send(bot, telegram_id, text)


async def _safe_send(bot: Bot, telegram_id: int, text: str):
    try:
        await bot.send_message(chat_id=telegram_id, text=text, parse_mode="HTML")
    except (TelegramForbiddenError, TelegramBadRequest):
        pass  # User blocked the bot or chat not found
