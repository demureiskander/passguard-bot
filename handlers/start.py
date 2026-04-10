from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from config import settings
from database.db import upsert_user
from texts.messages import START_NEW, START_RETURNING, HELP, HELP_LEGAL

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    name = user.first_name or "друг"

    is_new = await upsert_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name or name,
    )

    if is_new:
        text = START_NEW.format(name=name)
    else:
        text = START_RETURNING.format(name=name)

    await message.answer(text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    legal = ""
    if settings.AGREEMENT_URL and settings.PRIVACY_URL:
        legal = HELP_LEGAL.format(
            agreement=settings.AGREEMENT_URL,
            privacy=settings.PRIVACY_URL,
        )

    await message.answer(
        HELP.format(legal=legal),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
