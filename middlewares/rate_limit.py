import time
import logging
from collections import defaultdict
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from texts.messages import RATE_LIMIT

logger = logging.getLogger(__name__)

# 3 запроса за 2 секунды
MAX_REQUESTS = 3
WINDOW_SEC   = 2.0


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        # user_id → список timestamp'ов последних запросов
        self._history: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        # Не лимитируем команды
        text = event.text or ""
        if text.startswith("/"):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        history = self._history[user_id]

        # Убираем старые записи вне окна
        self._history[user_id] = [t for t in history if now - t < WINDOW_SEC]

        if len(self._history[user_id]) >= MAX_REQUESTS:
            await event.answer(RATE_LIMIT)
            return  # блокируем

        self._history[user_id].append(now)
        return await handler(event, data)
