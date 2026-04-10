import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import settings
from database.db import get_stats, get_all_user_ids
from keyboards.inline import kb_admin, kb_broadcast_confirm
from texts.messages import (
    ADMIN_PANEL, BROADCAST_PROMPT,
    BROADCAST_CONFIRM, BROADCAST_DONE, BROADCAST_CANCEL,
)

logger = logging.getLogger(__name__)
router = Router()


class BroadcastState(StatesGroup):
    waiting_text    = State()
    waiting_confirm = State()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# ─── /admin ──────────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not _is_admin(message.from_user.id):
        return

    stats = await get_stats()
    await message.answer(
        ADMIN_PANEL.format(**stats),
        parse_mode="HTML",
        reply_markup=kb_admin(),
    )


@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа.", show_alert=True)

    stats = await get_stats()
    await callback.message.edit_text(
        ADMIN_PANEL.format(**stats),
        parse_mode="HTML",
        reply_markup=kb_admin(),
    )
    await callback.answer()


# ─── Рассылка ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not _is_admin(callback.from_user.id):
        return await callback.answer("Нет доступа.", show_alert=True)

    await callback.answer()
    await callback.message.answer(BROADCAST_PROMPT)
    await state.set_state(BroadcastState.waiting_text)


@router.message(BroadcastState.waiting_text)
async def broadcast_got_text(message: Message, state: FSMContext):
    user_ids = await get_all_user_ids()
    await state.update_data(text=message.text, user_ids=user_ids)
    await state.set_state(BroadcastState.waiting_confirm)

    preview = message.text[:300] + ("…" if len(message.text) > 300 else "")
    await message.answer(
        BROADCAST_CONFIRM.format(count=len(user_ids), preview=preview),
        parse_mode="HTML",
        reply_markup=kb_broadcast_confirm(len(user_ids)),
    )


@router.callback_query(F.data == "admin:broadcast_confirm", BroadcastState.waiting_confirm)
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    await callback.answer()

    text     = data["text"]
    user_ids = data["user_ids"]
    ok = fail = 0

    for uid in user_ids:
        try:
            await callback.bot.send_message(uid, text, parse_mode="HTML")
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)  # ~20 msg/s, не превышаем лимиты

    await callback.message.answer(BROADCAST_DONE.format(ok=ok, fail=fail))


@router.callback_query(F.data == "admin:broadcast_cancel")
async def cb_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer(BROADCAST_CANCEL)
