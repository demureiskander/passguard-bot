import logging
import asyncio
import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database.db import increment_checks
from keyboards.inline import kb_show_ciphers, kb_cipher_categories, kb_cipher_results
from services.analyzer import analyze, mask_password, dots
from services.ciphers import format_by_category
from services.hibp import check_pwned
from texts.messages import (
    ANALYZING, CHECKING_VARIANTS,
    RESULT_HEADER, HIBP_CLEAN, HIBP_FOUND, HIBP_ERROR,
    STRENGTH_LINE, PATTERNS_HEADER, PATTERN_LINE,
    NO_ISSUES, TIPS_PROMPT, CATEGORY_CHOOSE,
    TOO_SHORT, TOO_LONG, ERROR_GENERIC, RATE_LIMIT_CB,
)

logger = logging.getLogger(__name__)
router = Router()

MIN_LEN = 4
MAX_LEN = 128

_cb_last: dict[int, float] = {}
CB_COOLDOWN = 3.0


def _cb_allowed(user_id: int) -> bool:
    now = time.monotonic()
    if now - _cb_last.get(user_id, 0) < CB_COOLDOWN:
        return False
    _cb_last[user_id] = now
    return True


@router.message(F.text & ~F.text.startswith("/"))
async def handle_password(message: Message):
    password = message.text.strip()
    if len(password) < MIN_LEN:
        await message.answer(TOO_SHORT)
        return
    if len(password) > MAX_LEN:
        await message.answer(TOO_LONG)
        return

    wait_msg = await message.answer(ANALYZING)
    try:
        hibp_task  = asyncio.create_task(check_pwned(password))
        analysis   = analyze(password)
        hibp_count = await hibp_task

        masked = mask_password(password)
        parts  = [RESULT_HEADER.format(masked=masked)]

        if hibp_count is None:
            parts.append(HIBP_ERROR)
        elif hibp_count == 0:
            parts.append(HIBP_CLEAN)
        else:
            parts.append(HIBP_FOUND.format(count=f"{hibp_count:,}"))

        parts.append(STRENGTH_LINE.format(dots=dots(analysis.score), score=analysis.score))

        if analysis.issues:
            parts.append(PATTERNS_HEADER)
            for issue in analysis.issues:
                parts.append(PATTERN_LINE.format(text=issue))
        else:
            parts.append(NO_ISSUES)

        show_btn = analysis.score < 4 or bool(analysis.issues)
        if show_btn:
            parts.append(TIPS_PROMPT)

        await wait_msg.edit_text(
            "".join(parts),
            parse_mode="HTML",
            reply_markup=kb_show_ciphers(password) if show_btn else None,
        )
        await increment_checks(message.from_user.id)

    except Exception as e:
        logger.exception("Ошибка: %s", type(e).__name__)
        await wait_msg.edit_text(ERROR_GENERIC)


@router.callback_query(F.data.startswith("ciphers:"))
async def cb_show_categories(callback: CallbackQuery):
    if not _cb_allowed(callback.from_user.id):
        await callback.answer(RATE_LIMIT_CB, show_alert=False)
        return
    password = callback.data.removeprefix("ciphers:")
    await callback.answer()
    await callback.message.edit_text(
        CATEGORY_CHOOSE,
        parse_mode="HTML",
        reply_markup=kb_cipher_categories(password),
    )


@router.callback_query(F.data.startswith("cat:"))
async def cb_show_ciphers_by_category(callback: CallbackQuery):
    if not _cb_allowed(callback.from_user.id):
        await callback.answer(RATE_LIMIT_CB, show_alert=False)
        return

    # формат: cat:CATEGORY:ATTEMPT:PASSWORD
    parts    = callback.data.split(":", 3)
    category = parts[1]
    attempt  = int(parts[2])
    password = parts[3]

    await callback.answer()
    await callback.message.edit_text(CHECKING_VARIANTS, parse_mode="HTML")

    text = await format_by_category(password, category, attempt)
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb_cipher_results(password, category, attempt),
    )
