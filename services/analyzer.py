"""
Анализатор паролей.
Пароли НЕ логируются и НЕ сохраняются — только числовые метрики.
"""

import re
import math
from dataclasses import dataclass, field
from typing import List

from texts.messages import (
    ISSUE_TOO_SHORT, ISSUE_SHORT,
    ISSUE_NO_UPPER, ISSUE_NO_LOWER, ISSUE_NO_DIGIT, ISSUE_NO_SPECIAL,
    ISSUE_NO_UPPER_SPEC, ISSUE_NO_DIGIT_SPEC, ISSUE_NO_ALL,
    ISSUE_REPEATS, ISSUE_KEYBOARD, ISSUE_DATE, ISSUE_NAME,
    ISSUE_DICT_WORD, ISSUE_DIGITS_ONLY, ISSUE_LETTERS_ONLY,
)

# ─── Паттерны ─────────────────────────────────────────────────────────────────

_KEYBOARD_WALKS = [
    "qwerty", "qwertz", "asdfgh", "zxcvbn",
    "йцукен", "фывапр", "ячсмит",
    "123456", "234567", "345678", "456789",
    "987654", "876543", "765432",
    "111111", "222222", "000000", "aaaaaa",
    "qwerty123", "password", "пароль",
    "abc123", "iloveyou", "monkey", "dragon",
]

_DATE_PATTERNS = [
    r"\b(0?[1-9]|[12]\d|3[01])(0?[1-9]|1[0-2])(\d{2}|\d{4})\b",
    r"\b(\d{4})(0?[1-9]|1[0-2])(0?[1-9]|[12]\d|3[01])\b",
    r"\b(19|20)\d{2}\b",
]

_COMMON_RU_NAMES = [
    "иван", "александр", "алексей", "дмитрий", "андрей", "михаил",
    "сергей", "артём", "артем", "максим", "илья", "роман", "кирилл",
    "мария", "анастасия", "анна", "ольга", "екатерина", "наталья",
    "татьяна", "елена", "юлия", "ирина", "светлана", "дарья",
    "nikita", "ivan", "sasha", "masha", "dasha", "katya", "natasha",
]

_COMMON_EN_WORDS = [
    "password", "pass", "login", "admin", "user", "test",
    "welcome", "hello", "master", "shadow", "monkey",
    "dragon", "princess", "sunshine", "football",
]


@dataclass
class AnalysisResult:
    score: int          = 0
    issues: List[str]   = field(default_factory=list)
    has_upper: bool     = False
    has_lower: bool     = False
    has_digit: bool     = False
    has_special: bool   = False
    has_cyrillic: bool  = False
    entropy: float      = 0.0


def _calc_entropy(password: str) -> float:
    charset = 0
    if re.search(r"[a-z]", password):                           charset += 26
    if re.search(r"[A-Z]", password):                           charset += 26
    if re.search(r"\d", password):                              charset += 10
    if re.search(r"[а-яёА-ЯЁ]", password):                     charset += 66
    if re.search(r"[^a-zA-Z\d\u0400-\u04FF]", password):       charset += 32
    if charset == 0:
        charset = 10
    return len(password) * math.log2(charset)


def dots(score: int, max_score: int = 5) -> str:
    filled = max(0, min(max_score, score))
    return "●" * filled + "○" * (max_score - filled)


def analyze(password: str) -> AnalysisResult:
    result = AnalysisResult()
    low = password.lower()

    result.has_upper    = bool(re.search(r"[A-Z]", password))
    result.has_lower    = bool(re.search(r"[a-z]", password))
    result.has_digit    = bool(re.search(r"\d", password))
    result.has_special  = bool(re.search(r"[^a-zA-Z\d\u0400-\u04FF]", password))
    result.has_cyrillic = bool(re.search(r"[а-яёА-ЯЁ]", password))
    result.entropy      = _calc_entropy(password)

    # Длина
    if len(password) < 8:
        result.issues.append(ISSUE_TOO_SHORT)
    elif len(password) < 12:
        result.issues.append(ISSUE_SHORT)

    # Состав — группируем в одно сообщение
    no_upper   = not result.has_upper and not re.search(r"[А-ЯЁ]", password)
    no_lower   = not result.has_lower and not result.has_cyrillic
    no_digit   = not result.has_digit
    no_special = not result.has_special

    if no_upper and no_digit and no_special:
        result.issues.append(ISSUE_NO_ALL)
    elif no_upper and no_special:
        result.issues.append(ISSUE_NO_UPPER_SPEC)
    elif no_digit and no_special:
        result.issues.append(ISSUE_NO_DIGIT_SPEC)
    else:
        if no_upper:
            result.issues.append(ISSUE_NO_UPPER)
        if no_lower:
            result.issues.append(ISSUE_NO_LOWER)
        if no_digit:
            result.issues.append(ISSUE_NO_DIGIT)
        if no_special:
            result.issues.append(ISSUE_NO_SPECIAL)

    # Повторы
    if re.search(r"(.)\1{2,}", password):
        result.issues.append(ISSUE_REPEATS)

    # Клавиатурные дорожки
    for walk in _KEYBOARD_WALKS:
        if walk in low or walk[::-1] in low:
            result.issues.append(ISSUE_KEYBOARD)
            break

    # Дата
    for pattern in _DATE_PATTERNS:
        if re.search(pattern, password):
            result.issues.append(ISSUE_DATE)
            break

    # Имена
    for name in _COMMON_RU_NAMES:
        if name in low:
            result.issues.append(ISSUE_NAME)
            break

    # Словарные слова
    for word in _COMMON_EN_WORDS:
        if word in low:
            result.issues.append(ISSUE_DICT_WORD.format(word=word))
            break

    # Только цифры / только буквы
    if re.fullmatch(r"\d+", password):
        result.issues.append(ISSUE_DIGITS_ONLY)
    elif re.fullmatch(r"[a-zA-Zа-яёА-ЯЁ]+", password):
        result.issues.append(ISSUE_LETTERS_ONLY)

    # Счёт
    if result.entropy >= 80:    base = 5
    elif result.entropy >= 60:  base = 4
    elif result.entropy >= 40:  base = 3
    elif result.entropy >= 25:  base = 2
    else:                       base = 1

    penalty = min(len(result.issues), 3)
    result.score = max(1, base - penalty)

    if not result.issues and base >= 4:
        result.score = 5

    return result


def mask_password(password: str) -> str:
    if len(password) <= 2:
        return "••"
    visible = max(1, min(2, len(password) // 4))
    hidden = len(password) - visible * 2
    return password[:visible] + "•" * hidden + password[-visible:]
