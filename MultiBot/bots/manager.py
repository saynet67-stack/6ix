import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TOKENS, VOICE_CHANNELS
from bots.client import MultiBotClient
from shared_data import init_bot, all_bots

PLACEHOLDER_TOKENS = {"YOUR_TOKEN_1_HERE", "YOUR_TOKEN_2_HERE", "YOUR_TOKEN_3_HERE", "YOUR_TOKEN_4_HERE", "YOUR_TOKEN_5_HERE"}

class BotManager:
    def __init__(self):
        self.bots = []
        num_bots = min(len(TOKENS), len(VOICE_CHANNELS))
        for i in range(num_bots):
            token = TOKENS[i]
            if not token or token in PLACEHOLDER_TOKENS or token.lower().startswith("your_token"):
                print(f"[SKIP] Bot {i+1}: no real token configured")
                continue
            init_bot(i + 1)
            bot = MultiBotClient(
                token=token,
                voice_id=VOICE_CHANNELS[i],
                number=i + 1
            )
            self.bots.append(bot)
            all_bots.append(bot)

    async def start_all(self):
        tasks = []
        for bot in self.bots:
            tasks.append(bot.start(bot.bot_token))

        print(f"Starting {len(self.bots)} bots...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                print(f"[ERR] Bot {i+1} failed to start: {r}")
