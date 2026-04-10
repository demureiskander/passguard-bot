import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import increment_checks
from keyboards.inline import kb_show_ciphers
from services.analyzer import analyze, mask_password, dots
from services.ciphers import format_suggestions
from services.hibp import check_pwned
from texts.messages import (
    ANALYZING, RESULT_HEADER,
    HIBP_CLEAN, HIBP_FOUND, HIBP_ERROR,
    STRENGTH_LINE, PATTERNS_HEADER, PATTERN_LINE,
    NO_ISSUES, TIPS_PROMPT,
    TOO_SHORT, TOO_LONG, ERROR_GENERIC,
)

logger = logging.getLogger(__name__)
router = Router()

MIN_LEN = 4
MAX_LEN = 128


@router.message(F.text & ~F.text.startswith("/"))
async def handle_password(message: Message):
    password = message.text.strip()

    # ── Валидация ─────────────────────────────────────────────────────────────
    if len(password) < MIN_LEN:
        await message.answer(TOO_SHORT)
        return

    if len(password) > MAX_LEN:
        await message.answer(TOO_LONG)
        return

    # ── «Анализирую…» — покажем сразу ────────────────────────────────────────
    wait_msg = await message.answer(ANALYZING)

    try:
        # ── Параллельно: HIBP + локальный анализ ─────────────────────────────
        import asyncio
        hibp_task     = asyncio.create_task(check_pwned(password))
        analysis      = analyze(password)
        hibp_count    = await hibp_task

        masked = mask_password(password)

        # ── Собираем результат ────────────────────────────────────────────────
        parts = [RESULT_HEADER.format(masked=masked)]

        # Утечки
        if hibp_count is None:
            parts.append(HIBP_ERROR)
        elif hibp_count == 0:
            parts.append(HIBP_CLEAN)
        else:
            parts.append(HIBP_FOUND.format(count=f"{hibp_count:,}"))

        # Сила пароля
        parts.append(STRENGTH_LINE.format(
            dots=dots(analysis.score),
            score=analysis.score,
        ))

        # Проблемы
        if analysis.issues:
            parts.append(PATTERNS_HEADER)
            for issue in analysis.issues:
                parts.append(PATTERN_LINE.format(text=issue))
        else:
            parts.append(NO_ISSUES)

        # Приглашение к усилению (если есть проблемы или слабый пароль)
        show_cipher_btn = analysis.score < 4 or bool(analysis.issues)
        if show_cipher_btn:
            parts.append(TIPS_PROMPT)

        result_text = "".join(parts)

        await wait_msg.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=kb_show_ciphers(password) if show_cipher_btn else None,
        )

        # ── Статистика ────────────────────────────────────────────────────────
        await increment_checks(message.from_user.id)

    except Exception as e:
        logger.exception("Ошибка при проверке пароля: %s", type(e).__name__)
        await wait_msg.edit_text(ERROR_GENERIC)


# ─── Callback: показать варианты усиления ────────────────────────────────────

@router.callback_query(F.data.startswith("ciphers:"))
async def cb_show_ciphers(callback: CallbackQuery):
    password = callback.data.removeprefix("ciphers:")

    await callback.answer()  # убираем «часики»

    text = format_suggestions(password)
    await callback.message.answer(text, parse_mode="HTML")
