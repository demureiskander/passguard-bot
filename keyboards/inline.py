from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings


def kb_show_ciphers(password: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔐 Показать варианты усиления", callback_data=f"ciphers:{password[:50]}")
    return builder.as_markup()


def kb_cipher_categories(password: str) -> InlineKeyboardMarkup:
    safe = password[:40]
    builder = InlineKeyboardBuilder()
    builder.button(text="🧠 Легко запомнить", callback_data=f"cat:easy:0:{safe}")
    builder.button(text="⚖️ Баланс",          callback_data=f"cat:balance:0:{safe}")
    builder.button(text="🔒 Максимум",         callback_data=f"cat:max:0:{safe}")
    builder.adjust(1)
    return builder.as_markup()


def kb_cipher_results(password: str, category: str, attempt: int) -> InlineKeyboardMarkup:
    safe = password[:40]
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Новые варианты", callback_data=f"cat:{category}:{attempt + 1}:{safe}")
    builder.button(text="← Назад",           callback_data=f"ciphers:{safe}")
    builder.adjust(1)
    return builder.as_markup()


def kb_coffee() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ 50 Stars",  callback_data="stars:50")
    builder.button(text="⭐ 100 Stars", callback_data="stars:100")
    builder.button(text="⭐ 200 Stars", callback_data="stars:200")
    builder.adjust(3)
    if settings.TRIBUTE_USERNAME:
        builder.row(InlineKeyboardButton(
            text="🌍 Tribute — любой банк или USDT",
            url=f"https://tribute.tg/{settings.TRIBUTE_USERNAME}",
        ))
    if settings.YOOMONEY_WALLET:
        builder.row(InlineKeyboardButton(
            text="💳 ЮMoney",
            url=f"https://yoomoney.ru/to/{settings.YOOMONEY_WALLET}",
        ))
    return builder.as_markup()


def kb_admin() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📣 Рассылка",   callback_data="admin:broadcast")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.adjust(2)
    return builder.as_markup()


def kb_broadcast_confirm(count: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"✅ Разослать {count} пользователям", callback_data="admin:broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="admin:broadcast_cancel")
    builder.adjust(1)
    return builder.as_markup()
