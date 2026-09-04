import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from bots.manager import BotManager
try:
    from database.db_manager import setup_database
except Exception as e:
    print(f"[DB] setup_database unavailable: {e}")
    setup_database = None

async def main():
    print("[START] Starting MultiBot...")
    
    # Initialize Database
    if setup_database:
        try:
            await setup_database()
            print("[DB] Database initialized")
        except Exception as e:
            print(f"[DB] init error: {e}")

    # Initialize Bot Manager
    print("[MANAGER] Initializing Bot Manager...")
    manager = BotManager()
    print(f"[MANAGER] Created {len(manager.bots)} bots")
    
    # Start all Discord bots
    print("[START] Starting all bots...")
    await manager.start_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
