import aiosqlite
import logging
from datetime import date

logger = logging.getLogger(__name__)
DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                first_seen  TEXT NOT NULL,
                last_seen   TEXT NOT NULL,
                checks      INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_checks (
                check_date  TEXT NOT NULL,
                count       INTEGER DEFAULT 0,
                PRIMARY KEY (check_date)
            )
        """)
        await db.commit()


async def upsert_user(user_id: int, username: str | None, full_name: str) -> bool:
    """Возвращает True если пользователь новый."""
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT first_seen FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()

        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, first_seen, last_seen) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, username, full_name, today, today),
            )
            await db.commit()
            return True
        else:
            await db.execute(
                "UPDATE users SET username=?, full_name=?, last_seen=? WHERE user_id=?",
                (username, full_name, today, user_id),
            )
            await db.commit()
            return False


async def increment_checks(user_id: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET checks = checks + 1 WHERE user_id = ?", (user_id,)
        )
        await db.execute(
            "INSERT INTO daily_checks (check_date, count) VALUES (?, 1) "
            "ON CONFLICT(check_date) DO UPDATE SET count = count + 1",
            (today,),
        )
        await db.commit()


async def get_user_checks(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT checks FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] if row else 0


async def get_stats() -> dict:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            users = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT count FROM daily_checks WHERE check_date = ?", (today,)
        ) as cur:
            row = await cur.fetchone()
            checks_today = row[0] if row else 0
        async with db.execute("SELECT SUM(checks) FROM users") as cur:
            row = await cur.fetchone()
            checks_total = row[0] or 0

    return {"users": users, "checks_today": checks_today, "checks_total": checks_total}


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]
