import hmac
import hashlib
import json
import time
import logging
from urllib.parse import unquote
from fastapi import HTTPException, Header
from bot.config import settings

logger = logging.getLogger(__name__)


def verify_telegram_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    parsed = {}
    for item in init_data.split("&"):
        if "=" in item:
            key, value = item.split("=", 1)
            parsed[key] = unquote(value)

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > 604800:
        raise HTTPException(status_code=401, detail="initData expired")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.BOT_TOKEN.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    expected = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    user_data = json.loads(parsed["user"])
    return user_data


async def get_current_twa_user(
    x_init_data: str = Header(None),
    x_user_id: str = Header(None),
):
    """
    Verifies Telegram WebApp user.
    Falls back to X-User-Id header for Telegram Desktop
    which doesn't provide initData.
    """
    if x_init_data:
        return verify_telegram_init_data(x_init_data)

    # Fallback for Telegram Desktop (no initData)
    if x_user_id:
        logger.warning(f"Using fallback X-User-Id: {x_user_id} (Telegram Desktop)")
        try:
            return {"id": int(x_user_id)}
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid user id")

    raise HTTPException(status_code=401, detail="Missing initData")