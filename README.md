# 🛡 PassKnight Bot

**A Telegram bot that checks your password against a database of real-world data breaches.**

[@PassKnightBot](https://t.me/PassKnightBot)

---

## How it works

1. You send a password
2. The bot checks it against the [HaveIBeenPwned](https://haveibeenpwned.com) database (14B+ breached passwords)
3. Rates its strength on a ●●●●○ scale
4. Detects weak patterns — birthdays, names, keyboard walks, repeated characters
5. Suggests strengthened variants using different encoding methods

## Privacy

Your password **never leaves your device in plain text.**

The bot uses [k-Anonymity](https://en.wikipedia.org/wiki/K-anonymity): only the first 5 characters of the SHA-1 hash are sent to the HIBP API — enough to find matches, impossible to reverse. Passwords are never stored or logged.

The source code is open specifically so you can verify this yourself.

## Features

- 🔴 Check against 14B+ real leaked passwords via HIBP
- 📊 Strength rating ●●●●○ based on entropy and pattern analysis
- 🔍 Pattern detection: names, dates, keyboard walks, repeated chars, dictionary words
- 🔐 Strengthening suggestions: L33tspeak, Caesar cipher, mixed case, separators, combos
- ☕ Support the developer via Telegram Stars

## Stack

Python 3.12 · aiogram 3.7 · aiosqlite · aiohttp · Railway

## Run locally

```bash
git clone https://github.com/demureiskander/passguard-bot.git
cd passguard-bot
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your BOT_TOKEN to .env
python bot.py
```

---

© 2025 Iskender. Source available for transparency. All rights reserved.
