# ======================
# CONFIGURATION (Railway env vars)
# ======================
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Load tokens from environment
TOKENS = []
for i in range(1, 6):
    token = os.environ.get(f"TOKEN_{i}")
    if token and token not in ("YOUR_TOKEN_1_HERE", "YOUR_TOKEN_2_HERE", "YOUR_TOKEN_3_HERE", "YOUR_TOKEN_4_HERE", "YOUR_TOKEN_5_HERE"):
        TOKENS.append(token)
        print(f"[CONFIG] Loaded TOKEN_{i}")
    else:
        print(f"[CONFIG] TOKEN_{i} not set or placeholder")

if not TOKENS:
    print("[CONFIG] WARNING: No valid tokens found!")

VOICE_CHANNELS = []
for i in range(1, 6):
    voice_id = os.environ.get(f"VOICE_ID_{i}")
    if voice_id:
        try:
            VOICE_CHANNELS.append(int(voice_id))
            print(f"[CONFIG] Loaded VOICE_ID_{i}: {voice_id}")
        except:
            print(f"[CONFIG] Invalid VOICE_ID_{i}: {voice_id}")
    else:
        VOICE_CHANNELS.append(0)
        print(f"[CONFIG] VOICE_ID_{i} not set")

MUSIC_CHANNEL = int(os.environ.get("MUSIC_CHANNEL", 0))
PREFIX = [".", ""]

# Lavalink Nodes from JSON env var
_ln = os.environ.get("LAVALINK_NODES")
if _ln:
    LAVALINK_NODES = json.loads(_ln)
else:
    # Use working Lavalink nodes
    LAVALINK_NODES = [
        {"uri": "http://lavalink.dev:2333", "password": "youshallnotpass"},
        {"uri": "http://node.korv.eu:2333", "password": "korv.lavalink"},
        {"uri": "https://lavalink.bots.gg:2333", "password": "lavalink.gg"},
        {"uri": "http://node1.lavalink.maddevs.xyz:2333", "password": "maddevs"},
    ]

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "high")
ENABLED_SOURCES = os.environ.get("ENABLED_SOURCES", "youtube,soundcloud,spotify,deezer")
DB_PATH = os.environ.get("DB_PATH", "database/data.db")