"""
Анализатор паролей.
Пароли НЕ логируются и НЕ сохраняются — только числовые метрики.
"""

import re
import math
from dataclasses import dataclass, field
from typing import List


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
    r"\b(0?[1-9]|[12]\d|3[01])(0?[1-9]|1[0-2])(\d{2}|\d{4})\b",  # ddmmyyyy
    r"\b(\d{4})(0?[1-9]|1[0-2])(0?[1-9]|[12]\d|3[01])\b",         # yyyymmdd
    r"\b(19|20)\d{2}\b",                                             # год: 1900-2099
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


# ─── Датакласс результата ─────────────────────────────────────────────────────

@dataclass
class AnalysisResult:
    score: int          = 0   # 0-5
    issues: List[str]   = field(default_factory=list)
    has_upper: bool     = False
    has_lower: bool     = False
    has_digit: bool     = False
    has_special: bool   = False
    has_cyrillic: bool  = False
    entropy: float      = 0.0


# ─── Вспомогательные функции ──────────────────────────────────────────────────

def _calc_entropy(password: str) -> float:
    """Реальная энтропия через размер алфавита × log2(длина)."""
    charset = 0
    if re.search(r"[a-z]", password):           charset += 26
    if re.search(r"[A-Z]", password):           charset += 26
    if re.search(r"\d", password):              charset += 10
    if re.search(r"[а-яёА-ЯЁ]", password):     charset += 66
    if re.search(r"[^a-zA-Z\d\u0400-\u04FF]", password): charset += 32
    if charset == 0:
        charset = 10
    return len(password) * math.log2(charset)


def dots(score: int, max_score: int = 5) -> str:
    filled = max(0, min(max_score, round(score * max_score / max_score)))
    # score уже в шкале max_score
    filled = max(0, min(max_score, score))
    return "●" * filled + "○" * (max_score - filled)


# ─── Основная функция ─────────────────────────────────────────────────────────

def analyze(password: str) -> AnalysisResult:
    result = AnalysisResult()
    low = password.lower()

    # Составы
    result.has_upper    = bool(re.search(r"[A-Z]", password))
    result.has_lower    = bool(re.search(r"[a-z]", password))
    result.has_digit    = bool(re.search(r"\d", password))
    result.has_special  = bool(re.search(r"[^a-zA-Z\d\u0400-\u04FF]", password))
    result.has_cyrillic = bool(re.search(r"[а-яёА-ЯЁ]", password))
    result.entropy      = _calc_entropy(password)

    # ── Проверки ──────────────────────────────────────────────────────────────

    # 1. Длина
    if len(password) < 8:
        result.issues.append("Слишком короткий — надёжный пароль от 12 символов")
    elif len(password) < 12:
        result.issues.append("Длина нормальная, но 12+ символов надёжнее")

    # 2. Состав символов
    missing = []
    if not result.has_upper and not result.has_cyrillic:
        missing.append("заглавных букв")
    if not result.has_lower and not result.has_cyrillic:
        missing.append("строчных букв")
    if not result.has_digit:
        missing.append("цифр")
    if not result.has_special:
        missing.append("спецсимволов (!@#$…)")
    if missing:
        result.issues.append("Нет " + ", ".join(missing))

    # 3. Повторяющиеся символы
    if re.search(r"(.)\1{2,}", password):
        result.issues.append("Есть повторяющиеся символы подряд (aaa, 111…)")

    # 4. Клавиатурные дорожки
    for walk in _KEYBOARD_WALKS:
        if walk in low or walk[::-1] in low:
            result.issues.append(f"Содержит клавиатурную дорожку («{walk}»)")
            break

    # 5. Паттерны даты
    for pattern in _DATE_PATTERNS:
        if re.search(pattern, password):
            result.issues.append("Похоже на дату или год рождения")
            break

    # 6. Имена
    for name in _COMMON_RU_NAMES:
        if name in low:
            result.issues.append("Содержит распространённое имя")
            break

    # 7. Словарные слова
    for word in _COMMON_EN_WORDS:
        if word in low:
            result.issues.append(f"Содержит словарное слово («{word}»)")
            break

    # 8. Только цифры
    if re.fullmatch(r"\d+", password):
        result.issues.append("Состоит только из цифр")

    # 9. Только буквы
    if re.fullmatch(r"[a-zA-Zа-яёА-ЯЁ]+", password):
        result.issues.append("Состоит только из букв")

    # ── Счёт ──────────────────────────────────────────────────────────────────
    # Базовый счёт: энтропия
    if result.entropy >= 80:
        base = 5
    elif result.entropy >= 60:
        base = 4
    elif result.entropy >= 40:
        base = 3
    elif result.entropy >= 25:
        base = 2
    else:
        base = 1

    # Штраф за паттерны
    penalty = min(len(result.issues), 3)
    result.score = max(1, base - penalty)

    # Бонус: нет ни одной проблемы
    if not result.issues and base >= 4:
        result.score = 5

    return result


def mask_password(password: str) -> str:
    """Маскируем пароль для показа: первый символ + точки + последний."""
    if len(password) <= 2:
        return "••"
    visible = max(1, min(2, len(password) // 4))
    hidden = len(password) - visible * 2
    return password[:visible] + "•" * hidden + password[-visible:]
