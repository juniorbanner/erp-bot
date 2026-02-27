from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from bot.config import settings


def client_main_keyboard(webapp_url: str | None = None) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    if webapp_url:
        builder.row(KeyboardButton(text="🛒 Магазин", web_app={"url": webapp_url}))
    builder.row(
        KeyboardButton(text="💰 Мой баланс"),
        KeyboardButton(text="📜 История покупок"),
    )
    builder.row(
        KeyboardButton(text="📞 Мой профиль"),
        KeyboardButton(text="ℹ️ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)


def request_phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Поделиться номером", request_contact=True))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def balance_history_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📈 Все долги", callback_data="history:debt"),
        InlineKeyboardButton(text="📉 Все погашения", callback_data="history:repaid"),
    )
    builder.row(InlineKeyboardButton(text="📋 Вся история", callback_data="history:all"))
    return builder.as_markup()
