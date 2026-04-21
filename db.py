import aiosqlite
from datetime import datetime, timezone, timedelta

DB_PATH = "bot.db"

def now_utc():
    return datetime.now(timezone.utc).isoformat()

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                last_seen TEXT NOT NULL,
                last_proactive TEXT,
                proactive_enabled INTEGER NOT NULL DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

async def touch_user(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT chat_id FROM users WHERE chat_id = ?", (chat_id,))
        row = await cur.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO users (chat_id, last_seen) VALUES (?, ?)",
                (chat_id, now_utc())
            )
        else:
            await db.execute(
                "UPDATE users SET last_seen = ? WHERE chat_id = ?",
                (now_utc(), chat_id)
            )
        await db.commit()

async def set_proactive_enabled(chat_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET proactive_enabled = ? WHERE chat_id = ?",
            (1 if enabled else 0, chat_id)
        )
        await db.commit()

async def add_message(chat_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, now_utc())
        )
        await db.commit()

async def get_recent_messages(chat_id: int, limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT role, content
            FROM messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (chat_id, limit))
        rows = await cur.fetchall()
    rows.reverse()
    return [{"role": role, "content": content} for role, content in rows]

async def get_due_users(hours: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            SELECT chat_id, last_seen, last_proactive, proactive_enabled
            FROM users
        """)
        rows = await cur.fetchall()

    due = []
    for chat_id, last_seen, last_proactive, proactive_enabled in rows:
        if not proactive_enabled:
            continue
        last_seen_dt = datetime.fromisoformat(last_seen)
        last_proactive_dt = datetime.fromisoformat(last_proactive) if last_proactive else None
        if last_seen_dt <= cutoff and (last_proactive_dt is None or last_proactive_dt <= cutoff):
            due.append(chat_id)
    return due

async def mark_proactive(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET last_proactive = ? WHERE chat_id = ?",
            (now_utc(), chat_id)
        )
        await db.commit()