import random
import string
import hashlib
from dataclasses import dataclass
from typing import List, Dict

from services.analyzer import dots, analyze

CATEGORIES = {
    "easy":    "🧠 Легко запомнить",
    "balance": "⚖️ Баланс",
    "max":     "🔒 Максимум",
}

TARGET_BALANCE = 10
TARGET_MAX     = 12

_CAESAR_EN = string.ascii_lowercase
_CAESAR_RU = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

_L33T = {
    'a': '@', 'e': '3', 'i': '!', 'o': '0',
    's': '$', 't': '+', 'l': '1', 'b': '6', 'g': '9',
}
_L33T_RU = {
    'а': '@', 'е': '3', 'и': '!', 'о': '0', 'с': '$', 'т': '+',
}

_KEYBOARD_ROW1 = "qwertyuiop"
_KEYBOARD_ROW2 = "asdfghjkl"
_KEYBOARD_ROW3 = "zxcvbnm"
_KEYBOARD_SHIFT: Dict[str, str] = {}
for row in [_KEYBOARD_ROW1, _KEYBOARD_ROW2, _KEYBOARD_ROW3]:
    for i, ch in enumerate(row[:-1]):
        _KEYBOARD_SHIFT[ch] = row[i + 1]
    _KEYBOARD_SHIFT[row[-1]] = row[0]

_SEPARATORS = [".", "-", "_", "~", "*"]
_SPECIALS   = ["!", "@", "#", "$", "*", "&", "^"]
_CAP_METHODS = ["first", "last", "both"]


@dataclass
class CipherResult:
    name: str
    result: str
    security: int
    memory: int


def _make(name: str, result: str, memory: int) -> CipherResult:
    return CipherResult(name=name, result=result,
                        security=analyze(result).score, memory=memory)


def _caesar(p: str, shift: int) -> str:
    result = []
    for ch in p:
        low = ch.lower()
        if low in _CAESAR_EN:
            idx = (_CAESAR_EN.index(low) + shift) % 26
            new = _CAESAR_EN[idx]
            result.append(new.upper() if ch.isupper() else new)
        elif low in _CAESAR_RU:
            idx = (_CAESAR_RU.index(low) + shift) % len(_CAESAR_RU)
            new = _CAESAR_RU[idx]
            result.append(new.upper() if ch.isupper() else new)
        else:
            result.append(ch)
    return "".join(result)


def _l33t_full(p: str) -> str:
    return "".join(_L33T.get(c.lower(), _L33T_RU.get(c.lower(), c)) for c in p)


def _mixed_case(p: str, start: int = 0) -> str:
    result, idx = [], 0
    for ch in p:
        if ch.isalpha():
            result.append(ch.upper() if (idx + start) % 2 == 0 else ch.lower())
            idx += 1
        else:
            result.append(ch)
    return "".join(result)


def _keyboard_shift(p: str) -> str:
    return "".join(_KEYBOARD_SHIFT.get(c.lower(), _KEYBOARD_SHIFT.get(c, c)) for c in p)


def _l33t_vowels(p: str, attempt: int = 0) -> str:
    vowel_sets = [
        {'a': '@', 'e': '3', 'o': '0', 'а': '@', 'е': '3', 'о': '0'},
        {'a': '4', 'e': '€', 'o': '()', 'а': '4', 'е': '€', 'о': '()'},
        {'a': '@', 'e': '&', 'o': '0', 'а': '@', 'е': '&', 'о': '0'},
        {'a': '@', 'e': '3', 'o': '[]', 'а': '@', 'е': '3', 'о': '[]'},
        {'a': '@', 'e': '€', 'o': '0', 'а': '@', 'е': '€', 'о': '0'},
    ]
    m = vowel_sets[attempt % len(vowel_sets)]
    return "".join(m.get(c.lower(), c) for c in p)


def _cap_plus_symbol(p: str, rng: random.Random) -> str:
    method = rng.choice(_CAP_METHODS)
    s = rng.choice(_SPECIALS)
    if method == "first":
        return p[0].upper() + p[1:] + s
    elif method == "last":
        return p[:-1] + p[-1].upper() + s
    else:
        return p[0].upper() + p[1:-1] + p[-1].upper() + s


def _separator(p: str, sep: str) -> str:
    return sep.join(p[i:i+3] for i in range(0, len(p), 3))


def _pad_memorable(base: str, password: str, attempt: int, target: int) -> str:
    """
    Дополняет пароль до target символов запоминаемым способом:
    берёт первые 2 символа пароля + спецсимвол — легко восстановить в памяти.
    """
    if len(base) >= target:
        return base
    needed = target - len(base)
    specials_pool = "!@#$*"
    upper_pool = string.ascii_uppercase
    # Детерминированный но читаемый хвост: заглавные + цифра + спецсимвол
    seed = hashlib.md5(f"{password}{attempt}".encode()).hexdigest()
    tail = []
    for ch in seed:
        if len(tail) >= needed:
            break
        if ch.isdigit():
            tail.append(ch)
        elif ch.isalpha():
            tail.append(ch.upper())
    # Добавляем спецсимвол если ещё нет
    if not any(c in specials_pool for c in tail):
        tail.insert(len(tail)//2, specials_pool[attempt % len(specials_pool)])
    return base + "".join(tail[:needed])


def _pad_max(base: str, password: str, attempt: int, target: int = TARGET_MAX) -> str:
    """Дополняет до target для категории max — более агрессивно."""
    if len(base) >= target:
        return base
    needed = target - len(base)
    seed = hashlib.md5(f"{password}{attempt}max".encode()).hexdigest()
    tail = []
    specials_pool = "!@#$*&^"
    for i, ch in enumerate(seed):
        if len(tail) >= needed:
            break
        if i % 4 == 0:
            tail.append(ch if ch.isdigit() else str(i % 10))
        elif i % 4 == 1:
            tail.append(ch.upper() if ch.isalpha() else string.ascii_uppercase[i % 26])
        elif i % 4 == 2 and not any(c in specials_pool for c in tail):
            tail.append(specials_pool[i % len(specials_pool)])
        else:
            tail.append(ch.upper() if ch.isalpha() else string.ascii_uppercase[i % 26])
    sep = [".", "-", "_"][attempt % 3]
    return base + sep + "".join(tail[:needed])


def _build_candidates(password: str, category: str, attempt: int) -> List[CipherResult]:
    rng = random.Random(f"{password}{category}{attempt}")
    results: List[CipherResult] = []

    if category == "easy":
        r = _l33t_vowels(password, attempt)
        if r != password:
            results.append(_make("Замена гласных", r, memory=4))

        results.append(_make("Заглавная + символ",
            _cap_plus_symbol(password, rng), memory=4))

        seps = rng.sample(_SEPARATORS, min(2, len(_SEPARATORS)))
        for sep in seps:
            r = _separator(password, sep)
            results.append(_make(f"Разделители «{sep}»", r, memory=5))

        r = _mixed_case(password, start=attempt % 2)
        if r != password:
            results.append(_make("Чередование регистра", r, memory=3))

    elif category == "balance":
        shifts = [3, 5, 7, 11, 13]
        shift = shifts[attempt % len(shifts)]

        # 1. Цезарь + дополнение до 10
        base = _caesar(password, shift)
        r = _pad_memorable(base, password, attempt, TARGET_BALANCE)
        if r != password:
            results.append(_make(f"Цезарь (+{shift}) + усиление", r, memory=3))

        # 2. L33t + заглавная + дополнение
        base = _mixed_case(_l33t_full(password), start=0)
        r = _pad_memorable(base, password, attempt + 1, TARGET_BALANCE)
        if r != password:
            results.append(_make("L33t + регистр + усиление", r, memory=3))

        # 3. Чередование регистра + спецсимвол + дополнение
        s = rng.choice(_SPECIALS)
        base = _mixed_case(password, start=attempt % 2) + s
        r = _pad_memorable(base, password, attempt + 2, TARGET_BALANCE)
        if r != password:
            results.append(_make("Регистр + символ + усиление", r, memory=3))

        # 4. Сдвиг клавиатуры + дополнение
        base = _keyboard_shift(password)
        r = _pad_memorable(base, password, attempt + 3, TARGET_BALANCE)
        if r != password:
            results.append(_make("Сдвиг клавиатуры + усиление", r, memory=2))

        # 5. Цезарь + L33t + символ в разных позициях
        s = rng.choice(_SPECIALS)
        pos = rng.choice(["start", "end"])
        base = _caesar(_l33t_full(password), shift)
        base = (s + base) if pos == "start" else (base + s)
        r = _pad_memorable(base, password, attempt + 4, TARGET_BALANCE)
        if r != password:
            results.append(_make("Цезарь + L33t + символ", r, memory=2))

    elif category == "max":
        shifts = [2, 4, 6, 8]
        shift = shifts[attempt % len(shifts)]

        base = _mixed_case(_l33t_full(_caesar(password, shift)))
        r = _pad_max(base, password, attempt)
        if r != password:
            results.append(_make("Комбо + расширение", r, memory=2))

        base = _caesar(_l33t_full(password), shift + 3)
        r = _pad_max(base, password, attempt + 1)
        if r != password:
            results.append(_make("L33t + Цезарь + расширение", r, memory=1))

        base = _l33t_full(_keyboard_shift(password))
        r = _pad_max(base, password, attempt + 2)
        if r != password:
            results.append(_make("Клавиатура + L33t + расширение", r, memory=1))

        s1 = rng.choice(_SPECIALS)
        s2 = rng.choice([c for c in _SPECIALS if c != s1])
        base = s1 + _mixed_case(_caesar(password, shift)) + s2
        r = _pad_max(base, password, attempt + 3)
        if r != password:
            results.append(_make("Обёртка + расширение", r, memory=2))

        mirror = password + password[::-1][:3]
        base = _l33t_full(_mixed_case(mirror))
        r = _pad_max(base, password, attempt + 4)
        if r != password:
            results.append(_make("Зеркало + комбо + расширение", r, memory=2))

    seen: set[str] = set()
    unique: List[CipherResult] = []
    for c in results:
        if c.result not in seen and c.result != password:
            seen.add(c.result)
            unique.append(c)
    return unique


async def get_by_category_safe(password: str, category: str, attempt: int) -> List[CipherResult]:
    import asyncio
    from services.hibp import check_pwned
    candidates = _build_candidates(password, category, attempt)
    counts = await asyncio.gather(*[check_pwned(c.result) for c in candidates])
    return [c for c, count in zip(candidates, counts) if count == 0]


async def format_by_category(password: str, category: str, attempt: int = 0) -> str:
    from services.analyzer import mask_password
    from texts.messages import CIPHERS_HEADER, CIPHER_BLOCK, CIPHER_FOOTER, CIPHERS_ALL_PWNED, REPO_URL

    masked    = mask_password(password)
    cat_label = CATEGORIES.get(category, "")
    suggestions = await get_by_category_safe(password, category, attempt)

    if not suggestions:
        return CIPHERS_ALL_PWNED.format(masked=masked, category=cat_label)

    parts = [CIPHERS_HEADER.format(masked=masked, category=cat_label)]
    for i, s in enumerate(suggestions, start=1):
        parts.append(CIPHER_BLOCK.format(
            num=i, name=s.name, result=s.result,
            sec_dots=dots(s.security), mem_dots=dots(s.memory),
        ))
    parts.append(CIPHER_FOOTER.format(repo=REPO_URL))
    return "".join(parts)
