"""
Варианты усиления пароля через разные методы/шифры.
Пароли НЕ логируются.
"""

import random
import string
from dataclasses import dataclass
from typing import List, Optional
from services.analyzer import dots


@dataclass
class CipherResult:
    name: str
    result: str
    description: str    # одно предложение что это
    security: int       # 0-5
    memory: int         # 0-5


# ─── Таблицы замен ────────────────────────────────────────────────────────────

_L33T_MAP = {
    'a': '@', 'e': '3', 'i': '!',
    'o': '0', 's': '$', 't': '+',
    'l': '1', 'b': '6', 'g': '9',
}

_L33T_MAP_RU = {
    'а': '@', 'е': '3', 'и': '!',
    'о': '0', 'с': '$', 'т': '+',
}

_CAESAR_ALPHA_RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
_CAESAR_ALPHA_EN = string.ascii_lowercase


# ─── Методы ───────────────────────────────────────────────────────────────────

def _apply_l33t(password: str) -> str:
    result = []
    for ch in password:
        lower = ch.lower()
        if lower in _L33T_MAP:
            result.append(_L33T_MAP[lower])
        elif lower in _L33T_MAP_RU:
            result.append(_L33T_MAP_RU[lower])
        else:
            result.append(ch)
    return "".join(result)


def _apply_caesar(password: str, shift: int = 3) -> str:
    result = []
    for ch in password:
        low = ch.lower()
        if low in _CAESAR_ALPHA_EN:
            idx = (_CAESAR_ALPHA_EN.index(low) + shift) % 26
            new = _CAESAR_ALPHA_EN[idx]
            result.append(new.upper() if ch.isupper() else new)
        elif low in _CAESAR_ALPHA_RU:
            idx = (_CAESAR_ALPHA_RU.index(low) + shift) % len(_CAESAR_ALPHA_RU)
            new = _CAESAR_ALPHA_RU[idx]
            result.append(new.upper() if ch.isupper() else new)
        else:
            result.append(ch)
    return "".join(result)


def _apply_camel_case(password: str) -> str:
    """Чередование регистра: iVaN1990 → каждый чётный символ в верхнем."""
    result = []
    letter_idx = 0
    for ch in password:
        if ch.isalpha():
            if letter_idx % 2 == 0:
                result.append(ch.upper())
            else:
                result.append(ch.lower())
            letter_idx += 1
        else:
            result.append(ch)
    return "".join(result)


def _apply_separator(password: str, sep: str = ".") -> str:
    """Разбивает пароль на чанки по 3 символа с разделителем."""
    chunks = [password[i:i+3] for i in range(0, len(password), 3)]
    return sep.join(chunks)


def _apply_padded(password: str) -> str:
    """Добавляет 2 спецсимвола в начало и конец."""
    specials = "!@#$%^&*"
    s1 = random.choice(specials)
    s2 = random.choice(specials)
    return s1 + password + s2


def _apply_capitalise_first(password: str) -> str:
    """Делает первую букву заглавной, последнюю — заглавной + спецсимвол."""
    if not password:
        return password
    result = password[0].upper() + password[1:]
    specials = "!#$@"
    return result + random.choice(specials)


def _apply_l33t_partial(password: str) -> str:
    """L33tspeak только для гласных — более читаемо."""
    vowel_map = {'a': '@', 'e': '3', 'o': '0',
                 'а': '@', 'е': '3', 'о': '0'}
    result = []
    for ch in password:
        low = ch.lower()
        if low in vowel_map:
            result.append(vowel_map[low])
        else:
            result.append(ch)
    return "".join(result)


# ─── Основная функция ─────────────────────────────────────────────────────────

def get_suggestions(password: str) -> List[CipherResult]:
    """Возвращает список вариантов усиления, от простых к сложным."""
    suggestions: List[CipherResult] = []

    # 1. Частичный L33t (только гласные) — лёгкий
    r1 = _apply_l33t_partial(password)
    if r1 != password:
        suggestions.append(CipherResult(
            name="Замена гласных",
            result=r1,
            description="Гласные заменяются похожими символами — легко запомнить",
            security=2,
            memory=4,
        ))

    # 2. Первая заглавная + спецсимвол
    r2 = _apply_capitalise_first(password)
    suggestions.append(CipherResult(
        name="Заглавная + символ",
        result=r2,
        description="Первая буква заглавная, в конце случайный спецсимвол",
        security=3,
        memory=4,
    ))

    # 3. Шифр Цезаря +3
    r3 = _apply_caesar(password, 3)
    if r3 != password:
        suggestions.append(CipherResult(
            name="Шифр Цезаря (+3)",
            result=r3,
            description="Каждая буква смещается на 3 позиции в алфавите",
            security=2,
            memory=3,
        ))

    # 4. Разделитель точками
    if len(password) >= 6:
        r4 = _apply_separator(password, ".")
        suggestions.append(CipherResult(
            name="Разделители",
            result=r4,
            description="Пароль разбит на части точками — удобно набирать",
            security=3,
            memory=5,
        ))

    # 5. Чередование регистра
    r5 = _apply_camel_case(password)
    if r5 != password:
        suggestions.append(CipherResult(
            name="Чередование регистра",
            result=r5,
            description="Чётные буквы заглавные — добавляет сложности без забывания",
            security=3,
            memory=3,
        ))

    # 6. Полный L33tspeak
    r6 = _apply_l33t(password)
    if r6 != password and r6 != suggestions[0].result if suggestions else True:
        suggestions.append(CipherResult(
            name="L33tspeak",
            result=r6,
            description="Полная замена букв символами — классика хакерской культуры",
            security=3,
            memory=2,
        ))

    # 7. Комбо: Цезарь + l33t + заглавная
    r7 = _apply_camel_case(_apply_l33t(_apply_caesar(password, 2)))
    if r7 != password:
        suggestions.append(CipherResult(
            name="Комбо-усиление",
            result=r7,
            description="Цезарь + l33t + чередование — максимальная защита базы",
            security=5,
            memory=2,
        ))

    # Убираем дубли по result
    seen = set()
    unique = []
    for s in suggestions:
        if s.result not in seen and s.result != password:
            seen.add(s.result)
            unique.append(s)

    return unique[:6]  # максимум 6 вариантов


def format_suggestions(password: str) -> str:
    from services.analyzer import mask_password
    from texts.messages import CIPHERS_HEADER, CIPHER_BLOCK, CIPHER_FOOTER

    masked = mask_password(password)
    parts = [CIPHERS_HEADER.format(masked=masked)]

    for i, s in enumerate(get_suggestions(password), start=1):
        parts.append(CIPHER_BLOCK.format(
            num=i,
            name=s.name,
            result=s.result,
            sec_dots=dots(s.security),
            mem_dots=dots(s.memory),
        ))

    parts.append(CIPHER_FOOTER)
    return "".join(parts)
