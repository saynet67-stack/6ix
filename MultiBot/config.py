# ======================
# CONFIGURATION (Railway env vars)
# ======================
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKENS = [
    os.environ.get("TOKEN_1", "YOUR_TOKEN_1_HERE"),
    os.environ.get("TOKEN_2", "YOUR_TOKEN_2_HERE"),
    os.environ.get("TOKEN_3", "YOUR_TOKEN_3_HERE"),
    os.environ.get("TOKEN_4", "YOUR_TOKEN_4_HERE"),
    os.environ.get("TOKEN_5", "YOUR_TOKEN_5_HERE"),
]

VOICE_CHANNELS = [
    int(os.environ.get("VOICE_ID_1", 0)),
    int(os.environ.get("VOICE_ID_2", 0)),
    int(os.environ.get("VOICE_ID_3", 0)),
    int(os.environ.get("VOICE_ID_4", 0)),
    int(os.environ.get("VOICE_ID_5", 0)),
]

MUSIC_CHANNEL = int(os.environ.get("MUSIC_CHANNEL", 0))
PREFIX = [".", ""]

# Lavalink Nodes from JSON env var
_ln = os.environ.get("LAVALINK_NODES")
if _ln:
    LAVALINK_NODES = json.loads(_ln)
else:
    LAVALINK_NODES = [
        {"uri": "http://node-us.fsh.ovh:2333", "password": "fsh.ovh-lavalink-is-cool"},
        {"uri": "http://node-eu.fsh.ovh:2333", "password": "fsh.ovh-lavalink-is-cool"},
        {"uri": "http://lavalinkv4.serenetia.com:80", "password": "https://dsc.gg/ajidevserver"},
    ]

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
AUDIO_QUALITY = os.environ.get("AUDIO_QUALITY", "high")
ENABLED_SOURCES = os.environ.get("ENABLED_SOURCES", "youtube,soundcloud,spotify,deezer")
DB_PATH = os.environ.get("DB_PATH", "database/data.db")