from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.formatters import fmt_uzs, fmt_date
from bot.keyboards.client_kb import balance_history_keyboard
from db.models.user import User
from db.models.transaction import TransactionType
from db.repositories.nasiya_repo import get_user_transactions

router = Router()


@router.message(F.text == "💰 Мой баланс")
async def cmd_balance(message: Message, db_user: User, **kwargs):
    balance = float(db_user.nasiya_balance)

    if balance <= 0:
        status = "✅ Долгов нет!"
        emoji = "✅"
    elif balance < 100_000:
        status = "⚠️ Небольшая задолженность"
        emoji = "⚠️"
    else:
        status = "❗ Значительная задолженность"
        emoji = "❗"

    text = (
        f"💰 <b>Мой баланс</b>\n\n"
        f"{emoji} {status}\n"
        f"Текущий долг: <b>{fmt_uzs(balance)}</b>\n\n"
        "Нажмите кнопку для просмотра истории:"
    )
    await message.answer(text, reply_markup=balance_history_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("history:"))
async def show_history(call: CallbackQuery, db_user: User, session: AsyncSession, **kwargs):
    filter_type = call.data.split(":")[1]
    txns = await get_user_transactions(session, db_user.id, limit=20)

    if filter_type == "debt":
        txns = [t for t in txns if t.type == TransactionType.DEBT_ADDED]
        title = "📈 История долгов"
    elif filter_type == "repaid":
        txns = [t for t in txns if t.type == TransactionType.DEBT_REPAID]
        title = "📉 История погашений"
    else:
        title = "📋 Вся история"

    if not txns:
        await call.message.edit_text("История пуста.")
        await call.answer()
        return

    text = f"<b>{title}</b>\n{'─' * 25}\n"
    for t in txns:
        sign = "+" if t.amount > 0 else ""
        type_emoji = "📈" if t.amount > 0 else "📉"
        text += (
            f"{type_emoji} {fmt_date(t.created_at)}\n"
            f"   {sign}{fmt_uzs(t.amount)} → остаток: {fmt_uzs(t.balance_after)}\n"
        )
        if t.comment:
            text += f"   💬 {t.comment}\n"

    await call.message.edit_text(text, parse_mode="HTML")
    await call.answer()
