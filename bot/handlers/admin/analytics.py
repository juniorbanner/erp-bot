from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.decorators import admin_only
from bot.utils.formatters import fmt_uzs
from bot.services.analytics_service import get_daily_report
from bot.keyboards.admin_kb import admin_main_keyboard

router = Router()


@router.message(F.text == "📊 Аналитика")
@admin_only
async def cmd_analytics(message: Message, session: AsyncSession, **kwargs):
    report = await get_daily_report(session)

    debtors_text = ""
    for i, user in enumerate(report["top_debtors"], 1):
        debtors_text += f"  {i}. {user.full_name} — {fmt_uzs(user.nasiya_balance)}\n"

    text = (
        f"📊 <b>Отчёт за {report['date'].strftime('%d.%m.%Y')}</b>\n"
        f"{'─' * 30}\n\n"
        f"💵 Выручка (наличные): <b>{fmt_uzs(report['cash_revenue'])}</b>\n"
        f"📈 Новые долги: <b>{fmt_uzs(report['new_debt'])}</b>\n"
        f"📉 Погашения: <b>{fmt_uzs(report['repayments'])}</b>\n"
        f"👥 Активных должников: <b>{report['debtors_count']}</b>\n"
    )
    if debtors_text:
        text += f"\n🏆 <b>Топ должников:</b>\n{debtors_text}"

    await message.answer(text, parse_mode="HTML", reply_markup=admin_main_keyboard())


@router.message(F.text == "🔍 Найти клиента")
@admin_only
async def cmd_find_client(message: Message, **kwargs):
    from aiogram.fsm.context import FSMContext
    await message.answer(
        "🔍 Введите Telegram ID или номер телефона клиента:",
    )


@router.message(F.text.startswith("/client"))
@admin_only
async def show_client_info(message: Message, session: AsyncSession, **kwargs):
    from db.repositories.user_repo import search_user
    from db.repositories.nasiya_repo import get_user_transactions
    from bot.utils.formatters import fmt_date

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /client <ID или телефон>")
        return

    client = await search_user(session, parts[1])
    if not client:
        await message.answer("❌ Клиент не найден.")
        return

    txns = await get_user_transactions(session, client.id, limit=5)
    txn_text = ""
    for t in txns:
        sign = "+" if t.amount > 0 else ""
        txn_text += f"  {fmt_date(t.created_at)}: {sign}{fmt_uzs(t.amount)}\n"

    text = (
        f"👤 <b>{client.full_name}</b>\n"
        f"🆔 Telegram ID: <code>{client.id}</code>\n"
        f"📞 Телефон: {client.phone or '—'}\n"
        f"💰 Долг: <b>{fmt_uzs(client.nasiya_balance)}</b>\n"
        f"📅 Регистрация: {fmt_date(client.created_at)}\n"
    )
    if txn_text:
        text += f"\n📜 <b>Последние транзакции:</b>\n{txn_text}"

    await message.answer(text, parse_mode="HTML")
