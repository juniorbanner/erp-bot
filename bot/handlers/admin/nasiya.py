from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.decorators import admin_only
from bot.utils.formatters import fmt_uzs
from bot.services.nasiya_service import NasiyaService
from bot.keyboards.admin_kb import cancel_keyboard, confirm_inline
from db.repositories.user_repo import search_user

router = Router()


class AddDebtFSM(StatesGroup):
    waiting_for_client = State()
    waiting_for_amount = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()


class RepayDebtFSM(StatesGroup):
    waiting_for_client = State()
    waiting_for_amount = State()
    waiting_for_confirm = State()


# ─── ADD DEBT ──────────────────────────────────────────────────────────────

@router.message(F.text == "📝 Записать долг")
@admin_only
async def cmd_add_debt(message: Message, state: FSMContext, **kwargs):
    await message.answer(
        "📝 <b>Запись долга</b>\n\n"
        "Введите Telegram ID или номер телефона клиента:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddDebtFSM.waiting_for_client)


@router.message(StateFilter(AddDebtFSM.waiting_for_client))
@admin_only
async def add_debt_client_search(
    message: Message, state: FSMContext, session: AsyncSession, **kwargs
):
    if message.text == "❌ Отмена":
        await state.clear()
        from bot.keyboards.admin_kb import admin_main_keyboard
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return

    client = await search_user(session, message.text.strip())
    if not client:
        await message.answer("❌ Клиент не найден. Попробуйте снова:")
        return

    await state.update_data(
        client_id=client.id,
        client_name=client.full_name,
        current_balance=float(client.nasiya_balance),
    )
    await message.answer(
        f"👤 Найден: <b>{client.full_name}</b>\n"
        f"📞 Телефон: {client.phone or '—'}\n"
        f"💰 Текущий долг: <b>{fmt_uzs(client.nasiya_balance)}</b>\n\n"
        "Введите <b>сумму долга</b> (в UZS):",
        parse_mode="HTML",
    )
    await state.set_state(AddDebtFSM.waiting_for_amount)


@router.message(StateFilter(AddDebtFSM.waiting_for_amount))
@admin_only
async def add_debt_amount(message: Message, state: FSMContext, **kwargs):
    if message.text == "❌ Отмена":
        await state.clear()
        from bot.keyboards.admin_kb import admin_main_keyboard
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return

    try:
        amount = float(message.text.replace(" ", "").replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите корректную сумму, например: 50000")
        return

    await state.update_data(amount=amount)
    data = await state.get_data()
    new_balance = data["current_balance"] + amount
    await message.answer(
        f"💬 Добавьте комментарий (необязательно)\n"
        f"или нажмите /skip для пропуска:",
    )
    await state.set_state(AddDebtFSM.waiting_for_comment)
    await state.update_data(new_balance=new_balance)


@router.message(StateFilter(AddDebtFSM.waiting_for_comment))
@admin_only
async def add_debt_comment(message: Message, state: FSMContext, **kwargs):
    comment = None if message.text in ("/skip", "❌ Отмена") else message.text.strip()
    if message.text == "❌ Отмена":
        await state.clear()
        from bot.keyboards.admin_kb import admin_main_keyboard
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return

    await state.update_data(comment=comment)
    data = await state.get_data()

    await message.answer(
        f"📋 <b>Подтвердите запись:</b>\n\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"➕ Новый долг: +{fmt_uzs(data['amount'])}\n"
        f"💰 Итого долг: {fmt_uzs(data['new_balance'])}\n"
        + (f"💬 Комментарий: {comment}" if comment else ""),
        reply_markup=confirm_inline("add_debt"),
        parse_mode="HTML",
    )
    await state.set_state(AddDebtFSM.waiting_for_confirm)


@router.callback_query(F.data == "add_debt:yes", StateFilter(AddDebtFSM.waiting_for_confirm))
@admin_only
async def confirm_add_debt(
    call: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot, **kwargs
):
    data = await state.get_data()
    service = NasiyaService(session, bot)
    try:
        txn = await service.add_debt(
            client_id=data["client_id"],
            amount=data["amount"],
            admin_id=call.from_user.id,
            comment=data.get("comment"),
        )
        await call.message.edit_text(
            f"✅ <b>Долг успешно записан!</b>\n\n"
            f"🆔 Транзакция: #{txn.id}\n"
            f"👤 Клиент: {data['client_name']}\n"
            f"➕ Сумма: +{fmt_uzs(data['amount'])}\n"
            f"💰 Новый баланс: {fmt_uzs(data['new_balance'])}\n\n"
            f"📲 Клиент получил уведомление.",
            parse_mode="HTML",
        )
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка: {str(e)}")
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "add_debt:no")
async def cancel_add_debt(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await call.message.edit_text("Отменено.")
    await call.answer()


# ─── REPAY DEBT ────────────────────────────────────────────────────────────

@router.message(F.text == "💳 Погасить долг")
@admin_only
async def cmd_repay_debt(message: Message, state: FSMContext, **kwargs):
    await message.answer(
        "💳 <b>Погашение долга</b>\n\n"
        "Введите Telegram ID или номер телефона клиента:",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(RepayDebtFSM.waiting_for_client)


@router.message(StateFilter(RepayDebtFSM.waiting_for_client))
@admin_only
async def repay_client_search(
    message: Message, state: FSMContext, session: AsyncSession, **kwargs
):
    if message.text == "❌ Отмена":
        await state.clear()
        from bot.keyboards.admin_kb import admin_main_keyboard
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return

    client = await search_user(session, message.text.strip())
    if not client:
        await message.answer("❌ Клиент не найден.")
        return
    if float(client.nasiya_balance) <= 0:
        await message.answer(
            f"ℹ️ У клиента <b>{client.full_name}</b> нет долга.",
            parse_mode="HTML",
        )
        await state.clear()
        return

    await state.update_data(
        client_id=client.id,
        client_name=client.full_name,
        current_balance=float(client.nasiya_balance),
    )
    await message.answer(
        f"👤 <b>{client.full_name}</b>\n"
        f"💰 Долг: {fmt_uzs(client.nasiya_balance)}\n\n"
        "Введите сумму погашения:",
        parse_mode="HTML",
    )
    await state.set_state(RepayDebtFSM.waiting_for_amount)


@router.message(StateFilter(RepayDebtFSM.waiting_for_amount))
@admin_only
async def repay_amount(message: Message, state: FSMContext, **kwargs):
    if message.text == "❌ Отмена":
        await state.clear()
        from bot.keyboards.admin_kb import admin_main_keyboard
        await message.answer("Отменено.", reply_markup=admin_main_keyboard())
        return

    try:
        amount = float(message.text.replace(" ", "").replace(",", "."))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введите корректную сумму.")
        return

    data = await state.get_data()
    new_balance = max(0, data["current_balance"] - amount)
    await state.update_data(amount=amount, new_balance=new_balance)
    await message.answer(
        f"📋 <b>Подтвердите погашение:</b>\n\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"💳 Погашение: -{fmt_uzs(amount)}\n"
        f"💰 Остаток долга: {fmt_uzs(new_balance)}",
        reply_markup=confirm_inline("repay_debt"),
        parse_mode="HTML",
    )
    await state.set_state(RepayDebtFSM.waiting_for_confirm)


@router.callback_query(F.data == "repay_debt:yes", StateFilter(RepayDebtFSM.waiting_for_confirm))
@admin_only
async def confirm_repay(
    call: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot, **kwargs
):
    data = await state.get_data()
    service = NasiyaService(session, bot)
    try:
        txn = await service.repay_debt(
            client_id=data["client_id"],
            amount=data["amount"],
            admin_id=call.from_user.id,
        )
        await call.message.edit_text(
            f"✅ <b>Погашение записано!</b>\n\n"
            f"🆔 Транзакция: #{txn.id}\n"
            f"💳 Сумма: -{fmt_uzs(data['amount'])}\n"
            f"💰 Остаток долга: {fmt_uzs(data['new_balance'])}",
            parse_mode="HTML",
        )
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка: {str(e)}")
    await state.clear()
    await call.answer()


@router.callback_query(F.data == "repay_debt:no")
async def cancel_repay(call: CallbackQuery, state: FSMContext, **kwargs):
    await state.clear()
    await call.message.edit_text("Отменено.")
    await call.answer()
