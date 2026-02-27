from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from db.repositories.user_repo import get_or_create_user


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        session = data.get("session")
        if tg_user and session:
            db_user = await get_or_create_user(session, tg_user.id, tg_user)
            data["db_user"] = db_user
            data["is_admin"] = db_user.is_admin
        return await handler(event, data)
