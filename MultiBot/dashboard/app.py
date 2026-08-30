from quart import Quart, render_template_string, jsonify, request
import sys
import os
import asyncio
import json
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_data import bot_states, all_bots, clear_song
from config import DB_PATH
try:
    import aiosqlite
except ImportError:
    aiosqlite = None

try:
    import discord
    import wavelink
except ImportError:
    discord = None
    wavelink = None

app = Quart(__name__)

_bot_manager = None

def set_bot_manager(manager):
    global _bot_manager
    _bot_manager = manager

# ── Helper ──

def get_bot(num):
    if _bot_manager and 1 <= num <= len(_bot_manager.bots):
        return _bot_manager.bots[num - 1]
    return None

async def get_first_guild(bot):
    for guild in bot.guilds:
        return guild
    return None

# ── Existing API ──

@app.route("/api/bots")
async def api_bots():
    return jsonify(bot_states)

def _get_fp(bot, guild_id):
    pcog = bot.get_cog("PlayerCog")
    if not pcog: return None, False
    if pcog.lavalink_ready:
        vc = next(iter(bot.voice_clients), None)
        if vc and isinstance(vc, wavelink.Player): return vc, True
        if vc: return vc, True
    fp = pcog.fplayers.get(guild_id)
    if fp and isinstance(fp, wavelink.Player) and fp.connected: return fp, True
    vc = next(iter(bot.voice_clients), None)
    if vc and isinstance(vc, wavelink.Player):
        pcog.get_fplayer(guild_id, vc)
        return vc, True
    return None, False

@app.route("/api/control/<int:bot_num>/<action>")
async def api_control(bot_num, action):
    if not _bot_manager:
        return jsonify({"error": "Manager unavailable"}), 503
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Invalid bot"}), 404
    guild = next(iter(bot.guilds), None)
    if not guild:
        return jsonify({"error": "No guild"}), 400
    player, is_wl = _get_fp(bot, guild.id)
    if not player:
        return jsonify({"error": "Bot not connected to voice"}), 400
    try:
        if action == "skip":
            await player.stop()
            return jsonify({"success": True, "message": "Skipped"})
        elif action == "pause":
            await player.pause(True)
            return jsonify({"success": True, "message": "Paused"})
        elif action == "resume":
            await player.pause(False)
            return jsonify({"success": True, "message": "Resumed"})
        elif action == "stop":
            if hasattr(player, 'queue') and player.queue: player.queue.clear()
            await player.stop()
            clear_song(bot_num)
            return jsonify({"success": True, "message": "Stopped"})
        elif action == "volup":
            v = min(player.volume + 10, 150)
            await player.set_volume(v)
            return jsonify({"success": True, "message": f"Volume {v}%"})
        elif action == "voldown":
            v = max(player.volume - 10, 10)
            await player.set_volume(v)
            return jsonify({"success": True, "message": f"Volume {v}%"})
        elif action == "mute":
            await player.set_volume(0)
            return jsonify({"success": True, "message": "Muted"})
        elif action == "unmute":
            await player.set_volume(100)
            return jsonify({"success": True, "message": "Volume 100%"})
        else:
            return jsonify({"error": "Unknown action"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── New Moderation API ──

@app.route("/api/mod/ban", methods=["POST"])
async def api_ban():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    reason = data.get("reason", "")
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    try:
        user = await bot.fetch_user(uid)
        await guild.ban(user, reason=reason)
        return jsonify({"success": True, "message": f"Banned {user}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/kick", methods=["POST"])
async def api_kick():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    reason = data.get("reason", "")
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    try:
        await member.kick(reason=reason)
        return jsonify({"success": True, "message": f"Kicked {member}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/mute", methods=["POST"])
async def api_mute():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    try:
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for ch in guild.channels:
                await ch.set_permissions(muted_role, speak=False, send_messages=False)
        await member.add_roles(muted_role)
        return jsonify({"success": True, "message": f"Muted {member}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/unmute", methods=["POST"])
async def api_unmute():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member:
        return jsonify({"error": "Member not found"}), 404
    try:
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
        return jsonify({"success": True, "message": f"Unmuted {member}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/clear", methods=["POST"])
async def api_clear():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    cid = int(data.get("channel_id", 0))
    amount = int(data.get("amount", 10))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    channel = guild.get_channel(cid) or guild.get_thread(cid)
    if not channel:
        return jsonify({"error": "Channel not found"}), 404
    try:
        await channel.purge(limit=min(amount, 100))
        return jsonify({"success": True, "message": f"Cleared {amount} messages"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Members & Mod APIs ──

@app.route("/api/mod/timeout", methods=["POST"])
async def api_timeout():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    minutes = int(data.get("minutes", 10))
    reason = data.get("reason", "")
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot: return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild: return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member: return jsonify({"error": "Member not found"}), 404
    try:
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        return jsonify({"success": True, "message": f"Timed out {member.display_name} {minutes}m"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/untimeout", methods=["POST"])
async def api_untimeout():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot: return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    member = guild.get_member(uid) if guild else None
    if not member: return jsonify({"error": "Member not found"}), 404
    try:
        await member.timeout(None)
        return jsonify({"success": True, "message": f"Timeout removed for {member.display_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/nick", methods=["POST"])
async def api_nick():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    nick = data.get("nick", None)
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot: return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild: return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member: return jsonify({"error": "Member not found"}), 404
    try:
        await member.edit(nick=nick)
        return jsonify({"success": True, "message": f"Nickname set for {member.display_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/mod/roles", methods=["POST"])
async def api_roles():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    uid = int(data.get("user_id", 0))
    role_id = int(data.get("role_id", 0))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot: return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild: return jsonify({"error": "Guild not found"}), 404
    member = guild.get_member(uid)
    if not member: return jsonify({"error": "Member not found"}), 404
    role = guild.get_role(role_id)
    if not role: return jsonify({"error": "Role not found"}), 404
    try:
        if role in member.roles:
            await member.remove_roles(role)
            msg = f"Removed {role.name} from {member.display_name}"
        else:
            await member.add_roles(role)
            msg = f"Added {role.name} to {member.display_name}"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/members")
async def api_members():
    gid = int(request.args.get("guild_id", 0))
    bot_num = int(request.args.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot: return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid) if gid else next(iter(bot.guilds), None)
    if not guild: return jsonify({"error": "Guild not found"}), 404
    members = list(guild.members)
    if len(members) < guild.member_count and guild.me and guild.me.guild_permissions.manage_messages:
        try:
            members = [m async for m in guild.fetch_members(limit=None)]
        except:
            pass
    member_data = []
    for m in members:
        member_data.append({
            "id": str(m.id),
            "name": m.display_name,
            "tag": str(m),
            "bot": m.bot,
            "avatar": m.display_avatar.url,
            "roles": [r.name for r in m.roles[1:]],
            "top_role": m.top_role.name,
            "timed_out": bool(m.timed_out_until and m.timed_out_until > discord.utils.utcnow()),
            "muted": any(r.name == "Muted" for r in m.roles),
            "status": str(m.status),
        })
    return jsonify({
        "guild": {"id": str(guild.id), "name": guild.name, "icon": guild.icon.url if guild.icon else None},
        "members": member_data,
    })

@app.route("/api/custommds")
async def api_custom_cmds():
    gid = int(request.args.get("guild_id", 0))
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT name, response, created_by FROM custom_commands WHERE guild_id = ? ORDER BY name",
                (gid,)
            )
            rows = await cur.fetchall()
            await cur.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/customadd", methods=["POST"])
async def api_custom_add():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    name = data.get("name", "")
    response = data.get("response", "")
    uid = int(data.get("user_id", 0))
    if not name or not response:
        return jsonify({"error": "name & response required"}), 400
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id INTEGER NOT NULL, name TEXT NOT NULL, response TEXT NOT NULL,
                    created_by INTEGER, created_at TEXT, PRIMARY KEY (guild_id, name)
                )
            ''')
            await db.execute(
                "INSERT OR REPLACE INTO custom_commands (guild_id, name, response, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
                (gid, name, response, uid, discord.utils.utcnow().isoformat())
            )
            await db.commit()
        return jsonify({"success": True, "message": f"Added :{name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/customdel", methods=["POST"])
async def api_custom_del():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    name = data.get("name", "")
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "DELETE FROM custom_commands WHERE guild_id = ? AND name = ?", (gid, name)
            )
            await db.commit()
            n = cur.rowcount
            await cur.close()
        return jsonify({"success": True, "message": f"Deleted :{name}" if n else "Not found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Music Play API ──

@app.route("/api/music/play", methods=["POST"])
async def api_play():
    data = await request.get_json()
    query = data.get("query", "")
    bot_num = int(data.get("bot", 1))
    if not query:
        return jsonify({"error": "No query"}), 400
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    pcog = bot.get_cog("PlayerCog")
    if not pcog:
        return jsonify({"error": "Music cog unavailable"}), 503
    try:
        guild = next(iter(bot.guilds), None)
        if not guild: return jsonify({"error": "No guild"}), 400
        vc = next(iter(bot.voice_clients), None)
        if vc and not isinstance(vc, wavelink.Player):
            try: await vc.disconnect(force=True)
            except: pass
            vc = None
        if not vc:
            if not pcog._sync_lavalink_flag():
                return jsonify({"error": "Lavalink unavailable"}), 503
            channel = bot.get_channel(bot.voice_id)
            if not channel: return jsonify({"error": "Voice channel not found"}), 404
            try: vc = await channel.connect(cls=wavelink.Player)
            except: return jsonify({"error": "Lavalink connect failed"}), 500
        from music.dj import search_one
        track = await search_one(query)
        if not track: return jsonify({"error": "No results"}), 404
        await vc.queue.put_wait(track)
        if not vc.playing: await vc.play(vc.queue.get())
        return jsonify({"success": True, "message": f"Playing {track.title}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Guild Info API ──

@app.route("/api/guilds")
async def api_guilds():
    result = {}
    for num, bot in enumerate(all_bots, 1):
        for guild in bot.guilds:
            result[str(guild.id)] = {
                "name": guild.name,
                "icon": guild.icon.url if guild.icon else None,
                "member_count": guild.member_count,
                "channels": [{"id": c.id, "name": c.name} for c in guild.text_channels[:50]],
                "voice_channels": [{"id": c.id, "name": c.name} for c in guild.voice_channels[:20]],
                "roles": [{"id": r.id, "name": r.name} for r in guild.roles if r.name != "@everyone"][:50],
                "owner_id": str(guild.owner_id),
            }
    return jsonify(result)

# ── Dashboard Page ──

LOGO_URL = "https://images-ext-1.discordapp.net/external/UMsr9g1HmIHs63QDffmlOZIioOeAGybToNF3TfsJdrc/%3Fsize%3D2048/https/cdn.discordapp.com/icons/782046278842318848/ba3a859b33f819ca2e677f2d1513fa08.png?format=webp&quality=lossless"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MultiBot — Nexus Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--neon-cyan:#00f0ff;--neon-magenta:#ff00ff;--neon-mint:#00ff88;--neon-purple:#7b2ff7;--neon-blue:#0044ff;--bg-deep:#03030a;--bg-card:rgba(10,10,30,0.6)}
body{font-family:'Cairo','Orbitron',sans-serif;min-height:100vh;background:var(--bg-deep);padding:20px;position:relative;overflow-x:hidden;color:#fff}
body::before{content:'';position:fixed;top:0;left:0;width:100vw;height:100vh;background:url('"""+LOGO_URL+"""') center/cover no-repeat;opacity:0.05;pointer-events:none;z-index:0;filter:blur(4px) saturate(1.5)}
body::after{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at 50% 30%,rgba(0,240,255,0.03) 0%,transparent 50%),radial-gradient(ellipse at 50% 70%,rgba(123,47,247,0.03) 0%,transparent 50%);pointer-events:none;z-index:0}
*{position:relative;z-index:1}
.tabs{display:flex;gap:8px;margin-bottom:25px;flex-wrap:wrap;justify-content:center}
.tab{padding:10px 22px;border-radius:12px;border:1px solid rgba(255,255,255,0.06);background:var(--bg-card);color:rgba(255,255,255,0.5);cursor:pointer;font-family:'Cairo',sans-serif;font-size:0.9em;font-weight:600;transition:.3s;backdrop-filter:blur(12px)}
.tab:hover{border-color:rgba(0,240,255,0.2);color:var(--neon-cyan)}
.tab.active{background:rgba(0,240,255,0.06);border-color:rgba(0,240,255,0.2);color:var(--neon-cyan);box-shadow:0 0 20px rgba(0,240,255,0.05)}
.page{display:none}
.page.active{display:block}
.header{text-align:center;margin-bottom:30px}
.header h1{font-family:'Orbitron',sans-serif;font-size:2.4em;font-weight:900;letter-spacing:4px;background:linear-gradient(135deg,var(--neon-cyan),var(--neon-magenta),var(--neon-mint));background-size:200% 200%;-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;animation:neonShift 4s ease-in-out infinite alternate}
@keyframes neonShift{0%{background-position:0% 50%}100%{background-position:100% 50%}}
.header p{color:rgba(255,255,255,0.25);font-size:0.9em;letter-spacing:6px;text-transform:uppercase;font-family:'Orbitron',sans-serif}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px;max-width:1400px;margin:0 auto}
.card{background:var(--bg-card);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.05);border-radius:18px;padding:22px;transition:.4s}
.card:hover{border-color:rgba(0,240,255,0.12);transform:translateY(-2px)}
.card h3{color:#fff;font-size:1em;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.card h3 small{color:rgba(255,255,255,0.25);font-weight:400;font-size:0.7em}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
input,select{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:8px;padding:8px 12px;color:#fff;font-family:'Cairo',sans-serif;font-size:0.85em;flex:1;min-width:100px;transition:.3s}
input:focus,select:focus{outline:none;border-color:var(--neon-cyan);box-shadow:0 0 15px rgba(0,240,255,0.05)}
input::placeholder{color:rgba(255,255,255,0.2)}
select option{background:#0a0a1e}
.btn{padding:8px 18px;border-radius:8px;border:1px solid rgba(255,255,255,0.08);background:rgba(255,255,255,0.04);color:rgba(255,255,255,0.7);cursor:pointer;font-family:'Cairo',sans-serif;font-size:0.8em;font-weight:600;transition:.25s;white-space:nowrap;display:inline-flex;align-items:center;gap:5px}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 15px rgba(0,0,0,0.3)}
.btn-primary{background:rgba(0,240,255,0.06);border-color:rgba(0,240,255,0.15);color:var(--neon-cyan)}
.btn-primary:hover{background:rgba(0,240,255,0.1);box-shadow:0 0 20px rgba(0,240,255,0.05)}
.btn-danger{background:rgba(255,68,68,0.06);border-color:rgba(255,68,68,0.15);color:#ff6b6b}
.btn-danger:hover{background:rgba(255,68,68,0.1);box-shadow:0 0 20px rgba(255,68,68,0.05)}
.btn-success{background:rgba(0,255,136,0.06);border-color:rgba(0,255,136,0.15);color:var(--neon-mint)}
.btn-success:hover{background:rgba(0,255,136,0.1);box-shadow:0 0 20px rgba(0,255,136,0.05)}
.btn-warn{background:rgba(255,204,0,0.06);border-color:rgba(255,204,0,0.15);color:#ffcc00}
.btn-warn:hover{background:rgba(255,204,0,0.1);box-shadow:0 0 20px rgba(255,204,0,0.05)}
.btn:disabled{opacity:0.2;cursor:not-allowed;transform:none!important;box-shadow:none!important}
.toast{position:fixed;bottom:30px;left:50%;transform:translateX(-50%) translateY(100px);background:rgba(5,5,16,0.9);backdrop-filter:blur(20px);border:1px solid rgba(0,240,255,0.15);border-radius:12px;padding:12px 28px;color:#fff;font-family:'Cairo',sans-serif;font-size:0.85em;transition:transform .5s;pointer-events:none;z-index:100;box-shadow:0 0 30px rgba(0,240,255,0.05)}
.toast.show{transform:translateX(-50%) translateY(0)}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-left:6px}
.status-dot.online{background:var(--neon-cyan);box-shadow:0 0 10px var(--neon-cyan);animation:dotPulse 2s infinite}
.status-dot.offline{background:#ff4444}
@keyframes dotPulse{0%,100%{opacity:1}50%{opacity:0.5}}
.bot-badge{display:inline-flex;align-items:center;gap:6px;padding:4px 12px;border-radius:50px;font-size:0.75em;font-weight:600;font-family:'Orbitron',sans-serif;margin:2px}
.bot-badge.online{background:rgba(0,240,255,0.08);color:var(--neon-cyan);border:1px solid rgba(0,240,255,0.1)}
.bot-badge.offline{background:rgba(255,50,50,0.08);color:#ff4444;border:1px solid rgba(255,50,50,0.1)}
.bots-bar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
@media(max-width:600px){.header h1{font-size:1.6em}.grid{grid-template-columns:1fr}}
.search-row{display:flex;gap:10px;margin-bottom:12px}
.search-row input{flex:3}
.search-row select{flex:1}
.search-row button{flex-shrink:0}
.mod-log{background:rgba(0,0,0,0.2);border-radius:8px;padding:10px;margin-top:8px;max-height:120px;overflow-y:auto;font-size:0.8em;color:rgba(255,255,255,0.4)}
</style>
</head>
<body>
<div class="header">
<h1>ULTIBOT</h1>
<p>Nexus Control Center</p>
</div>

<div class="tabs">
<div class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</div>
<div class="tab" onclick="switchTab('music')">🎵 Music</div>
<div class="tab" onclick="switchTab('moderation')">⚔️ Moderation</div>
<div class="tab" onclick="switchTab('members')">👥 Members</div>
<div class="tab" onclick="switchTab('custom')">🛠️ Custom Cmds</div>
<div class="tab" onclick="switchTab('voice')">🎤 Temp Voice</div>
<div class="tab" onclick="switchTab('settings')">⚙️ Settings</div>
</div>

<div id="page-dashboard" class="page active">
<div class="grid" id="botsGrid"><div style="text-align:center;padding:60px;color:rgba(255,255,255,0.2)"><div class="spinner" style="width:40px;height:40px;border:2px solid rgba(0,240,255,0.08);border-top-color:var(--neon-cyan);border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 20px"></div>LOADING...</div></div>
</div>

<div id="page-music" class="page">

<div class="card" style="max-width:600px;margin:0 auto">
<h3>🎵 <small>Music Controls</small></h3>
<div class="bots-bar" id="musicBotsBar"></div>
<div class="search-row">
<select id="musicBotSelect"><option value="1">Bot 1</option><option value="2">Bot 2</option><option value="3">Bot 3</option><option value="4">Bot 4</option><option value="5">Bot 5</option></select>
<input id="playQuery" placeholder="Search YouTube or paste URL..." onkeydown="if(event.key==='Enter')playMusic()">
<button class="btn btn-primary" onclick="playMusic()">▶ Play</button>
</div>
<div class="row" style="justify-content:center;margin-top:10px">
<button class="btn btn-warn" onclick="ctrl('skip')">⏭ Skip</button>
<button class="btn btn-danger" onclick="ctrl('pause')">⏸ Pause</button>
<button class="btn btn-success" onclick="ctrl('resume')">▶ Resume</button>
<button class="btn btn-danger" onclick="ctrl('stop')">⏹ Stop</button>
<button class="btn btn-primary" onclick="ctrl('voldown')">🔉 −10</button>
<button class="btn btn-primary" onclick="ctrl('volup')">🔊 +10</button>
</div>
<div class="mod-log" id="musicStatus">Idle</div>
</div>
</div>

<div id="page-moderation" class="page">
<div class="grid">
<div class="card">
<h3>🔨 Ban</h3>
<div class="row"><input id="banUser" placeholder="User ID"><input id="banReason" placeholder="Reason (optional)"></div>
<button class="btn btn-danger" onclick="modAction('ban')">Ban</button>
</div>
<div class="card">
<h3>👢 Kick</h3>
<div class="row"><input id="kickUser" placeholder="User ID"><input id="kickReason" placeholder="Reason"></div>
<button class="btn btn-warn" onclick="modAction('kick')">Kick</button>
</div>
<div class="card">
<h3>🔇 Mute</h3>
<div class="row"><input id="muteUser" placeholder="User ID"></div>
<button class="btn btn-primary" onclick="modAction('mute')">Mute</button>
<button class="btn btn-success" onclick="modAction('unmute')">Unmute</button>
</div>
<div class="card">
<h3>🧹 Clear</h3>
<div class="row"><input id="clearChannel" placeholder="Channel ID"><input id="clearAmount" placeholder="Count" value="10"></div>
<button class="btn btn-primary" onclick="modAction('clear')">Clear</button>
</div>
</div>
<div class="mod-log" id="modLog" style="max-width:600px;margin:15px auto">Ready</div>
</div>

<div id="page-voice" class="page">
<div class="card" style="max-width:500px;margin:0 auto">
<h3>🎤 Temp Voice <small>Create & manage</small></h3>
<div class="row"><input id="vcName" placeholder="Room name"><select id="vcLock"><option value="no">Open</option><option value="yes">Locked</option></select></div>
<button class="btn btn-primary" onclick="createVoice()">➕ Create</button>
<button class="btn btn-danger" onclick="deleteAllVoice()" style="margin-top:10px">🗑 Delete All</button>
<div class="mod-log" id="vcStatus">Ready</div>
</div>
</div>

<div id="page-members" class="page">
<div class="card" style="max-width:900px;margin:0 auto">
<h3>👥 Members <small>Mod actions on the fly</small></h3>
<div class="row">
<select id="membersBot"><option value="1">Bot 1</option><option value="2">Bot 2</option><option value="3">Bot 3</option><option value="4">Bot 4</option><option value="5">Bot 5</option></select>
<input id="memberSearch" placeholder="Search by name..." oninput="renderMembers()">
<button class="btn btn-primary" onclick="loadMembers()">🔄 Refresh</button>
</div>
<div class="mod-log" id="membersStatus">Loading members...</div>
<div id="membersList" style="margin-top:10px"></div>
</div>
</div>

<div id="page-custom" class="page">
<div class="card" style="max-width:600px;margin:0 auto">
<h3>🛠️ Custom Commands <small>Add, list, delete</small></h3>
<div class="row">
<select id="customBot"><option value="1">Bot 1</option><option value="2">Bot 2</option><option value="3">Bot 3</option><option value="4">Bot 4</option><option value="5">Bot 5</option></select>
</div>
<div class="row"><input id="customName" placeholder="Command name (no spaces)"><input id="customResp" placeholder="Response text (use {user} {args})"></div>
<button class="btn btn-success" onclick="addCustom()">➕ Add</button>
<button class="btn btn-primary" onclick="loadCustom()" style="margin-right:8px">🔄 Refresh</button>
<div class="mod-log" id="customStatus">Ready</div>
<div id="customList" style="margin-top:10px"></div>
</div>
</div>

<div id="page-settings" class="page">
<div class="grid">
<div class="card">
<h3>🏠 Welcome Channel</h3>
<div class="row"><input id="welcomeChan" placeholder="Channel ID"></div>
<button class="btn btn-primary" onclick="setWelcome('channel')">Set</button>
</div>
<div class="card">
<h3>🎖 Welcome Role</h3>
<div class="row"><input id="welcomeRole" placeholder="Role ID"></div>
<button class="btn btn-primary" onclick="setWelcome('role')">Set</button>
<button class="btn btn-danger" onclick="setWelcome('roleremove')">Remove</button>
</div>
</div>
<div class="mod-log" id="settingsLog" style="max-width:600px;margin:15px auto">Ready</div>
</div>

<div class="toast" id="toast"></div>

<script>
function showToast(msg,err){const e=document.getElementById('toast');e.textContent=msg;e.style.borderColor=err?'rgba(255,50,50,0.3)':'rgba(0,240,255,0.2)';e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2500)}

function switchTab(t){document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));document.querySelectorAll('.page').forEach(e=>e.classList.remove('active'));document.querySelector(`.tab[onclick*="'${t}'"]`).classList.add('active');document.getElementById('page-'+t).classList.add('active')}

let selBot=1;
document.getElementById('musicBotSelect')?.addEventListener('change',e=>selBot=parseInt(e.target.value));

async function ctrl(a){const r=await fetch('/api/control/'+selBot+'/'+a),d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('musicStatus').textContent=d.message||d.error}

async function playMusic(){const q=document.getElementById('playQuery').value;if(!q)return;const r=await fetch('/api/music/play',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({query:q,bot:selBot})}),d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('musicStatus').textContent=d.message||d.error}

const gData={};
async function loadGuilds(){try{const r=await fetch('/api/guilds'),d=await r.json();Object.assign(gData,d)}catch(e){}}

async function modAction(a){const m={ban:'ban',kick:'kick',mute:'mute',unmute:'unmute',clear:'clear'};let uid,reason,ch,amt;const gids=Object.keys(gData);if(!gids.length)return showToast('No guilds found',1);const gid=gids[0];
if(a==='ban'){uid=document.getElementById('banUser').value;reason=document.getElementById('banReason').value}
else if(a==='kick'){uid=document.getElementById('kickUser').value;reason=document.getElementById('kickReason').value}
else if(a==='mute'||a==='unmute'){uid=document.getElementById('muteUser').value}
else if(a==='clear'){ch=document.getElementById('clearChannel').value;amt=parseInt(document.getElementById('clearAmount').value)||10}
const body={guild_id:parseInt(gid),bot:selBot};
if(uid)body.user_id=parseInt(uid);
if(reason)body.reason=reason;
if(ch)body.channel_id=parseInt(ch);
if(amt)body.amount=amt;
const r=await fetch('/api/mod/'+a,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('modLog').textContent=d.message||d.error}

async function createVoice(){const n=document.getElementById('vcName').value;const l=document.getElementById('vcLock').value;if(!n)return showToast('Enter a name',1);const gids=Object.keys(gData);if(!gids.length)return showToast('No guilds',1);const r=await fetch('/api/tempvoice/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),name:n,locked:l==='yes',bot:selBot})});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('vcStatus').textContent=d.message||d.error}

async function deleteAllVoice(){const gids=Object.keys(gData);if(!gids.length)return showToast('No guilds',1);const r=await fetch('/api/tempvoice/deleteall',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),bot:selBot})});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('vcStatus').textContent=d.message||d.error}

async function setWelcome(t){const gids=Object.keys(gData);if(!gids.length)return showToast('No guilds',1);if(t==='channel'){const v=document.getElementById('welcomeChan').value;if(!v)return showToast('Enter channel ID',1);const r=await fetch('/api/settings/welcome',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),channel_id:parseInt(v),bot:selBot})});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('settingsLog').textContent=d.message||d.error}
if(t==='role'){const v=document.getElementById('welcomeRole').value;if(!v)return showToast('Enter role ID',1);const r=await fetch('/api/settings/welcomerole',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),role_id:parseInt(v),bot:selBot})});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('settingsLog').textContent=d.message||d.error}
if(t==='roleremove'){const r=await fetch('/api/settings/welcomerole',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),role_id:0,bot:selBot})});const d=await r.json();d.success?showToast(d.message):showToast(d.error||'Error',1);document.getElementById('settingsLog').textContent=d.message||d.error}}

async function fetchBots(){try{const r=await fetch('/api/bots'),data=await r.json();renderBots(data)}catch(e){}}

function renderBots(data){const grid=document.getElementById('botsGrid');const entries=Object.entries(data);let html='',online=0,playing=0,servers=0;
for(const[num,bot]of entries){const isOnline=bot.status==='online';if(isOnline)online++;if(bot.current_song)playing++;servers+=bot.guild_count||0;const sc=isOnline?'online':'offline';const song=bot.current_song;
html+=`<div class="card" style="border-color:${isOnline?'rgba(0,240,255,0.1)':'rgba(255,50,50,0.1)'}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
<div><strong style="font-family:'Orbitron',sans-serif;color:${isOnline?'var(--neon-cyan)':'#ff4444'}">BOT ${num}</strong><br><small style="color:rgba(255,255,255,0.3)">${bot.name||'—'}</small></div>
<div class="bot-badge ${sc}"><span class="status-dot ${sc}"></span>${isOnline?'ONLINE':'OFFLINE'}</div>
</div>
${song?`<div style="background:rgba(0,0,0,0.3);border-radius:10px;padding:12px"><div style="display:flex;gap:12px">${song.thumbnail?`<img src="${song.thumbnail}" style="width:50px;height:50px;border-radius:8px;object-fit:cover">`:'<div style="width:50px;height:50px;border-radius:8px;background:rgba(0,240,255,0.05);display:flex;align-items:center;justify-content:center;font-size:1.2em">♪</div>'}<div style="flex:1;min-width:0"><div style="color:#fff;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"><a href="${song.uri||'#'}" target="_blank" style="color:var(--neon-cyan);text-decoration:none">${song.title||'—'}</a></div><div style="color:rgba(255,255,255,0.3);font-size:0.8em">${song.author||'—'} • ${song.duration_fmt||'0:00'}</div><div style="color:rgba(255,255,255,0.2);font-size:0.75em">👤 ${song.requester||'—'}</div></div></div></div>`:`<div style="background:rgba(0,0,0,0.2);border-radius:10px;padding:18px;text-align:center;color:rgba(255,255,255,0.15);font-size:0.85em">◇ IDLE</div>`}
<div style="display:flex;gap:12px;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.03)">
<div style="text-align:center;flex:1"><div style="font-weight:700;color:rgba(255,255,255,0.8);font-size:0.9em">${bot.guild_count||0}</div><div style="color:rgba(255,255,255,0.2);font-size:0.7em">GUILDS</div></div>
<div style="text-align:center;flex:1"><div style="font-weight:700;color:rgba(255,255,255,0.8);font-size:0.9em">${bot.voice_channel||'—'}</div><div style="color:rgba(255,255,255,0.2);font-size:0.7em">VOICE</div></div>
<div style="text-align:center;flex:1"><div style="font-weight:700;color:rgba(255,255,255,0.8);font-size:0.9em">${song?'▶':'⏹'}</div><div style="color:rgba(255,255,255,0.2);font-size:0.7em">STATUS</div></div>
</div>
</div>`}
grid.innerHTML=html||'<div style="text-align:center;padding:60px;color:rgba(255,255,255,0.2);grid-column:1/-1">NO DATA</div>';
document.getElementById('statsOnline').textContent=online;document.getElementById('statsPlaying').textContent=playing;document.getElementById('statsServers').textContent=servers}

let memData=[],memGid='',memBot=1;
document.getElementById('membersBot')?.addEventListener('change',e=>{memBot=parseInt(e.target.value);loadMembers()});
document.getElementById('customBot')?.addEventListener('change',e=>{loadCustom()});

async function loadMembers(){const gids=Object.keys(gData);if(!gids.length)return renderMembers();memGid=gids[0];const r=await fetch('/api/members?guild_id='+memGid+'&bot='+memBot);const d=await r.json();if(d.members){memData=d.members;renderMembers();document.getElementById('membersStatus').textContent='Members: '+d.members.length+' — '+d.guild.name}else{document.getElementById('membersStatus').textContent=d.error||'Error';memData=[];renderMembers()}}

function renderMembers(){const box=document.getElementById('membersList');const q=(document.getElementById('memberSearch')?.value||'').toLowerCase();const list=memData.filter(m=>m.name.toLowerCase().includes(q));if(!list.length){box.innerHTML='<div style="color:rgba(255,255,255,0.2);text-align:center;padding:30px">NO MEMBERS</div>';return}
let html='';
for(const m of list){const isBot=m.bot?'<span style="color:var(--neon-purple);font-size:0.7em">BOT</span>':'';
html+=`<div style="display:flex;align-items:center;gap:10px;padding:8px;border-bottom:1px solid rgba(255,255,255,0.03)">
<img src="${m.avatar}" style="width:36px;height:36px;border-radius:50%">
<div style="flex:1;min-width:0"><div style="color:#fff;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${m.name} ${isBot}</div>
<div style="color:rgba(255,255,255,0.25);font-size:0.7em">${m.top_role} ${m.timed_out?'• ⏱ Timeout':''} ${m.muted?'• 🔇 Muted':''} • ${m.status}</div></div>
<button class="btn btn-primary" style="padding:4px 10px;font-size:0.7em" onclick="nickMember('${m.id}')">✏️ Nick</button>
<button class="btn btn-success" style="padding:4px 10px;font-size:0.7em" ${m.timed_out?'disabled':''} onclick="modMember('timeout','${m.id}')">⏱ Timeout</button>
<button class="btn btn-success" style="padding:4px 10px;font-size:0.7em" ${m.timed_out?'':'disabled'} onclick="modMember('untimeout','${m.id}')">▶ UnTimeout</button>
<button class="btn btn-primary" style="padding:4px 10px;font-size:0.7em" ${m.muted?'disabled':''} onclick="modMember('mute','${m.id}')">🔇 Mute</button>
<button class="btn btn-success" style="padding:4px 10px;font-size:0.7em" ${m.muted?'':'disabled'} onclick="modMember('unmute','${m.id}')">🔊 Unmute</button>
<button class="btn btn-warn" style="padding:4px 10px;font-size:0.7em" onclick="modMember('kick','${m.id}')">👢 Kick</button>
<button class="btn btn-danger" style="padding:4px 10px;font-size:0.7em" onclick="modMember('ban','${m.id}')">🚫 Ban</button>
</div>`}
box.innerHTML=html}

async function nickMember(uid){const v=prompt('New nickname:');if(!v)return;const r=await fetch('/api/mod/nick',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(memGid),user_id:parseInt(uid),nick:v,bot:memBot})});const d=await r.json();d.success?(showToast(d.message),loadMembers()):showToast(d.error||'Error',1)}

async function modMember(a,uid){const body={guild_id:parseInt(memGid),user_id:parseInt(uid),bot:memBot};if(a==='timeout'){const m=prompt('Minutes:');if(!m)return;body.minutes=parseInt(m)}
const r=await fetch('/api/mod/'+a,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const d=await r.json();d.success?(showToast(d.message),loadMembers()):showToast(d.error||'Error',1)}

async function loadCustom(){const gids=Object.keys(gData);if(!gids.length)return;const gid=gids[0];const r=await fetch('/api/custommds?guild_id='+gid);const d=await r.json();const box=document.getElementById('customList');if(!Array.isArray(d)||!d.length){box.innerHTML='<div style="color:rgba(255,255,255,0.2);text-align:center;padding:20px">NO CUSTOM COMMANDS</div>';document.getElementById('customStatus').textContent='Ready';return}
let html='';for(const c of d){html+=`<div style="display:flex;align-items:center;gap:10px;padding:8px;border-bottom:1px solid rgba(255,255,255,0.03)"><code style="color:var(--neon-cyan);flex:1">:${c.name}</code><span style="color:rgba(255,255,255,0.3);font-size:0.75em;flex:2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${c.response}</span><button class="btn btn-danger" style="padding:4px 10px;font-size:0.7em" onclick="delCustom('${c.name}')">🗑</button></div>`}
box.innerHTML=html;document.getElementById('customStatus').textContent=d.length+' commands'}

async function addCustom(){const name=document.getElementById('customName').value.trim();const resp=document.getElementById('customResp').value.trim();if(!name||!resp)return showToast('Name & response required',1);const gids=Object.keys(gData);if(!gids.length)return showToast('No guilds',1);const r=await fetch('/api/customadd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),name,response:resp,user_id:0,bot:memBot})});const d=await r.json();d.success?(showToast(d.message),document.getElementById('customName').value='',document.getElementById('customResp').value='',loadCustom()):showToast(d.error||'Error',1)}

async function delCustom(name){const gids=Object.keys(gData);if(!gids.length)return;const r=await fetch('/api/customdel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({guild_id:parseInt(gids[0]),name})});const d=await r.json();d.success?(showToast(d.message),loadCustom()):showToast(d.error||'Error',1)}

loadGuilds();fetchBots();setInterval(fetchBots,3000);
</script>
</body>
</html>"""

@app.route("/")
async def home():
    return await render_template_string(TEMPLATE)

# ── Temp Voice API ──

@app.route("/api/tempvoice/create", methods=["POST"])
async def api_create_voice():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    name = data.get("name", "Temp Voice")
    locked = data.get("locked", False)
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    try:
        overwrites = {guild.default_role: discord.PermissionOverwrite(connect=not locked, speak=not locked)}
        vc = await guild.create_voice_channel(name=name, overwrites=overwrites)
        return jsonify({"success": True, "message": f"Created {name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/tempvoice/deleteall", methods=["POST"])
async def api_delete_all_voice():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    guild = bot.get_guild(gid)
    if not guild:
        return jsonify({"error": "Guild not found"}), 404
    try:
        tc = bot.get_cog("TempVoice")
        if tc:
            config = tc.load_config()
            active = config.get(str(gid), {}).get("active_rooms", {})
            cnt = 0
            for cid in list(active.keys()):
                ch = guild.get_channel(int(cid))
                if ch:
                    await ch.delete(); cnt += 1
            return jsonify({"success": True, "message": f"Deleted {cnt} rooms"})
        return jsonify({"error": "TempVoice cog not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Settings API ──

@app.route("/api/settings/welcome", methods=["POST"])
async def api_set_welcome():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    channel_id = data.get("channel_id", 0)
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    try:
        import moderation.welcome as wc
        wc.WELCOME_CHANNEL_ID = channel_id
        return jsonify({"success": True, "message": "Welcome channel updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/settings/welcomerole", methods=["POST"])
async def api_set_welcome_role():
    data = await request.get_json()
    gid = int(data.get("guild_id", 0))
    role_id = data.get("role_id", 0)
    bot_num = int(data.get("bot", 1))
    bot = get_bot(bot_num)
    if not bot:
        return jsonify({"error": "Bot unavailable"}), 503
    try:
        wc = bot.get_cog("WelcomeCog")
        if wc:
            wc.welcome_role_id = role_id if role_id else None
            return jsonify({"success": True, "message": "Welcome role updated"})
        return jsonify({"error": "WelcomeCog not loaded"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def start_dashboard():

    port = int(os.environ.get("PORT", "5000"))
    print(f"Dashboard starting on port {port}")
    await app.run_task(host="0.0.0.0", port=port)
