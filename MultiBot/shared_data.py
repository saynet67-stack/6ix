bot_states = {}
all_bots = []

def init_bot(number):
    bot_states[number] = {
        "status": "offline",
        "name": None,
        "guild_count": 0,
        "voice_channel": None,
        "current_song": None
    }

def update_song(number, title, author, uri, thumbnail, duration, requester):
    if number in bot_states:
        bot_states[number]["current_song"] = {
            "title": title,
            "author": author,
            "uri": uri,
            "thumbnail": thumbnail,
            "duration": duration,
            "duration_fmt": format_duration(duration),
            "requester": requester
        }

def clear_song(number):
    if number in bot_states:
        bot_states[number]["current_song"] = None

def format_duration(ms):
    if not ms:
        return "0:00"
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60
    if hours:
        return f"{hours}:{minutes % 60:02d}:{seconds % 60:02d}"
    return f"{minutes}:{seconds % 60:02d}"

def make_progress_bar(position, duration, length=16):
    if not duration or position > duration:
        return "▰" * length
    ratio = position / duration
    filled = round(ratio * length)
    filled = min(filled, length)
    bar = "▰" * filled + "▱" * (length - filled)
    p = format_duration(position)
    d = format_duration(duration)
    return f"{bar}  {p} / {d}"
