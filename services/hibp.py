"""
Проверка пароля по базе HaveIBeenPwned через k-Anonymity.
Только первые 5 символов SHA-1 хэша покидают устройство.
Пароль в открытом виде никуда не отправляется.
"""

import hashlib
import aiohttp
import logging

logger = logging.getLogger(__name__)

_HIBP_URL = "https://api.pwnedpasswords.com/range/"
_HEADERS = {
    "Add-Padding": "true",
    "User-Agent": "PassGuardBot/2.0 (Telegram)",
}


async def check_pwned(password: str) -> int | None:
    """
    Возвращает количество утечек (0 = чисто) или None при ошибке.
    Пароль НЕ логируется.
    """
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                _HIBP_URL + prefix,
                headers=_HEADERS,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()

        for line in text.splitlines():
            if not line:
                continue
            parts = line.split(":")
            if len(parts) != 2:
                continue
            if parts[0].strip() == suffix:
                return int(parts[1].strip())
        return 0

    except Exception as e:
        logger.warning("HIBP недоступен: %s", type(e).__name__)
        return None
