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
        logger.error("initData is empty!")
        raise HTTPException(status_code=401, detail="Missing initData")

    logger.info(f"initData received, length: {len(init_data)}")

    parsed = {}
    for item in init_data.split("&"):
        if "=" in item:
            key, value = item.split("=", 1)
            parsed[key] = unquote(value)

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash in initData")

    auth_date = int(parsed.get("auth_date", 0))
    age = time.time() - auth_date
    logger.info(f"auth_date age: {age:.0f} seconds")

    # Allow up to 7 days
    if age > 604800:
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

    logger.info(f"expected: {expected[:10]}..., received: {received_hash[:10]}...")

    if not hmac.compare_digest(expected, received_hash):
        logger.error("Hash mismatch!")
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    user_data = json.loads(parsed["user"])
    return user_data


async def get_current_twa_user(x_init_data: str = Header(None)):
    return verify_telegram_init_data(x_init_data or "")