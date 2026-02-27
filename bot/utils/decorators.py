from functools import wraps
from aiogram.types import Message, CallbackQuery


def admin_only(func):
    """Restrict handler to admin users only."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        is_admin = kwargs.get("is_admin", False)
        if not is_admin:
            event = args[0]
            if isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён. Только для администраторов.")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён.", show_alert=True)
            return
        return await func(*args, **kwargs)
    return wrapper
