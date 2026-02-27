from aiogram import Router, F
from aiogram.types import Message, Contact
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, StateFilter
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.formatters import fmt_uzs, fmt_date
from bot.keyboards.client_kb import client_main_keyboard, request_phone_keyboard
from bot.keyboards.admin_kb import admin_main_keyboard
from bot.config import settings
from db.models.user import User

router = Router()


class RegisterFSM(StatesGroup):
    waiting_phone = State()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    session: AsyncSession,
    db_user: User,
    is_admin: bool,
    **kwargs,
):
    if is_admin:
        await message.answer(
            f"👋 Добро пожаловать, <b>{message.from_user.first_name}</b>!\n"
            f"Вы вошли как <b>Администратор</b>.",
            reply_markup=admin_main_keyboard(),
            parse_mode="HTML",
        )
        return

    # Check if phone registered
    if not db_user.phone:
        await message.answer(
            f"👋 Ассалому алайкум, <b>{message.from_user.first_name}</b>!\n\n"
            "Для доступа к функциям магазина, поделитесь своим номером телефона:",
            reply_markup=request_phone_keyboard(),
            parse_mode="HTML",
        )
        return

    await message.answer(
        f"👋 Ассалому алайкум, <b>{db_user.full_name}</b>!\n\n"
        "Выберите действие:",
        reply_markup=client_main_keyboard(settings.WEBAPP_URL),
        parse_mode="HTML",
    )


@router.message(F.contact)
async def handle_contact(
    message: Message,
    session: AsyncSession,
    db_user: User,
    **kwargs,
):
    contact: Contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("❌ Пожалуйста, поделитесь своим номером телефона.")
        return

    # Normalize phone
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    db_user.phone = phone
    if not db_user.full_name and contact.first_name:
        db_user.full_name = f"{contact.first_name} {contact.last_name or ''}".strip()

    await session.flush()

    await message.answer(
        f"✅ Номер <b>{phone}</b> сохранён!\n\n"
        "Теперь вы можете пользоваться всеми функциями магазина.",
        reply_markup=client_main_keyboard(settings.WEBAPP_URL),
        parse_mode="HTML",
    )


@router.message(F.text == "📞 Мой профиль")
async def cmd_profile(message: Message, db_user: User, **kwargs):
    text = (
        f"👤 <b>Мой профиль</b>\n\n"
        f"Имя: {db_user.full_name}\n"
        f"Телефон: {db_user.phone or '—'}\n"
        f"Дата регистрации: {fmt_date(db_user.created_at)}\n"
        f"💰 Долг: <b>{fmt_uzs(db_user.nasiya_balance)}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "ℹ️ Помощь")
async def cmd_help(message: Message, **kwargs):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "🛒 <b>Магазин</b> — просмотр товаров и оформление заказа\n"
        "💰 <b>Мой баланс</b> — текущий долг и история\n"
        "📜 <b>История покупок</b> — все ваши заказы\n"
        "📞 <b>Мой профиль</b> — ваши данные\n\n"
        "По вопросам обращайтесь к продавцу.",
        parse_mode="HTML",
    )
