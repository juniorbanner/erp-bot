import hmac
import hashlib
import json
import time
from urllib.parse import unquote
from fastapi import HTTPException, Header
from bot.config import settings


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Official Telegram WebApp initData validation.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
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

    # Check expiration (24 hours)
    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise HTTPException(status_code=401, detail="initData expired")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    expected = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    user_data = json.loads(parsed["user"])
    return user_data


async def get_current_twa_user(x_init_data: str = Header(None)):
    """FastAPI dependency that returns verified Telegram user dict."""
    return verify_telegram_init_data(x_init_data or "")
