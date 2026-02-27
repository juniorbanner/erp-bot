from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📝 Записать долг"),
        KeyboardButton(text="💳 Погасить долг"),
    )
    builder.row(
        KeyboardButton(text="🔍 Найти клиента"),
        KeyboardButton(text="📊 Аналитика"),
    )
    builder.row(
        KeyboardButton(text="📦 Управление товарами"),
        KeyboardButton(text="📣 Рассылка"),
    )
    return builder.as_markup(resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отмена"))
    return builder.as_markup(resize_keyboard=True)


def confirm_inline(action: str = "confirm") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"{action}:yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"{action}:no"),
    )
    return builder.as_markup()


def product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить цену", callback_data=f"prod_price:{product_id}"),
        InlineKeyboardButton(text="📦 Изменить остаток", callback_data=f"prod_stock:{product_id}"),
    )
    builder.row(
        InlineKeyboardButton(
            text="🚫 Скрыть" if True else "✅ Показать",
            callback_data=f"prod_toggle:{product_id}"
        ),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"prod_delete:{product_id}"),
    )
    return builder.as_markup()


def categories_inline(categories) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"{cat.icon or '📁'} {cat.name}",
                callback_data=f"admin_cat:{cat.id}"
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_cat:new"))
    return builder.as_markup()


def broadcast_segments_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Долг > 100 000 UZS", callback_data="broadcast:debt_100k"))
    builder.row(InlineKeyboardButton(text="💰 Долг > 500 000 UZS", callback_data="broadcast:debt_500k"))
    builder.row(InlineKeyboardButton(text="👥 Все клиенты", callback_data="broadcast:all"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast:cancel"))
    return builder.as_markup()
