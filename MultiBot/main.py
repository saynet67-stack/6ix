import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from bots.manager import BotManager
from dashboard.app import start_dashboard, set_bot_manager
try:
    from database.db_manager import setup_database
except Exception as e:
    print(f"[DB] setup_database unavailable: {e}")
    setup_database = None

async def main():
    # Initialize Database
    if setup_database:
        try:
            await setup_database()
        except Exception as e:
            print(f"[DB] init error: {e}")

    # Initialize Bot Manager
    manager = BotManager()
    set_bot_manager(manager)
    
    # Start Dashboard as an asyncio task
    asyncio.create_task(start_dashboard())
    
    # Start all Discord bots
    await manager.start_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
