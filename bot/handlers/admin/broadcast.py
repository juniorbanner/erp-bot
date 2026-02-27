import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.utils.decorators import admin_only
from bot.keyboards.admin_kb import broadcast_segments_keyboard, admin_main_keyboard
from db.models.user import User

router = Router()


class BroadcastFSM(StatesGroup):
    waiting_segment = State()
    waiting_message = State()


@router.message(F.text == "📣 Рассылка")
@admin_only
async def cmd_broadcast(message: Message, state: FSMContext, **kwargs):
    await message.answer(
        "📣 <b>Рассылка сообщений</b>\n\nВыберите сегмент получателей:",
        reply_markup=broadcast_segments_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(BroadcastFSM.waiting_segment)


@router.callback_query(F.data.startswith("broadcast:"), StateFilter(BroadcastFSM.waiting_segment))
@admin_only
async def broadcast_select_segment(call: CallbackQuery, state: FSMContext, **kwargs):
    segment = call.data.split(":")[1]
    if segment == "cancel":
        await state.clear()
        await call.message.edit_text("Отменено.")
        await call.answer()
        return

    await state.update_data(segment=segment)
    await call.message.edit_text(
        "✍️ Введите текст рассылки:\n\n"
        "<i>Поддерживается HTML-форматирование: <b>жирный</b>, <i>курсив</i></i>",
        parse_mode="HTML",
    )
    await state.set_state(BroadcastFSM.waiting_message)
    await call.answer()


@router.message(StateFilter(BroadcastFSM.waiting_message))
@admin_only
async def broadcast_send(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot, **kwargs
):
    data = await state.get_data()
    segment = data["segment"]
    text = message.text

    # Get recipients based on segment
    if segment == "debt_100k":
        result = await session.execute(
            select(User.id).where(User.nasiya_balance >= 100_000, User.is_active == True)  # noqa: E712
        )
    elif segment == "debt_500k":
        result = await session.execute(
            select(User.id).where(User.nasiya_balance >= 500_000, User.is_active == True)  # noqa: E712
        )
    else:  # all
        result = await session.execute(
            select(User.id).where(User.is_admin == False, User.is_active == True)  # noqa: E712
        )

    user_ids = list(result.scalars().all())
    if not user_ids:
        await message.answer("❌ Нет получателей в этом сегменте.", reply_markup=admin_main_keyboard())
        await state.clear()
        return

    progress_msg = await message.answer(
        f"⏳ Отправляю {len(user_ids)} получателям..."
    )

    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.send_message(
                chat_id=uid,
                text=f"📢 <b>Сообщение от магазина:</b>\n\n{text}",
                parse_mode="HTML",
            )
            sent += 1
        except TelegramForbiddenError:
            failed += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # Telegram API limit: 20 msg/sec

    await progress_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="HTML",
    )
    await state.clear()
