from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery

from keyboards.inline import kb_coffee
from texts.messages import COFFEE

router = Router()


@router.message(Command("coffee"))
async def cmd_coffee(message: Message):
    await message.answer(COFFEE, parse_mode="HTML", reply_markup=kb_coffee())


@router.callback_query(F.data.startswith("stars:"))
async def cb_stars(callback: CallbackQuery):
    amount = int(callback.data.split(":")[1])
    await callback.answer()
    await callback.message.answer_invoice(
        title="☕ Поддержать PassGuard",
        description="Спасибо — ты помогаешь держать бота живым!",
        payload=f"coffee_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label="Stars", amount=amount)],
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def payment_done(message: Message):
    stars = message.successful_payment.total_amount
    await message.answer(
        f"☕ Получил {stars} Stars — огромное спасибо!\n"
        "Буду делать бота лучше 🙌"
    )
