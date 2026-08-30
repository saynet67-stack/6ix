import aiosqlite
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

async def setup_database():
    """Initializes the database tables if they do not exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                guild_id INTEGER PRIMARY KEY,
                prefix TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS custom_commands (
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                response TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT,
                PRIMARY KEY (guild_id, name)
            )
        ''')
        await db.commit()
        print("[OK] Database setup complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_database())
