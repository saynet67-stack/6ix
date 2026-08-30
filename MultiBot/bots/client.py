import discord
from discord.ext import commands
import sys
import os
import traceback
import asyncio
import wavelink
from wavelink import NodeStatus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PREFIX, LAVALINK_NODES
from shared_data import bot_states

class MultiBotClient(commands.Bot):
    def __init__(self, token, voice_id, number):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.members = True

        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None
        )
        self.bot_token = token
        self.voice_id = voice_id
        self.number = number

    async def setup_hook(self):
        cogs = ["music.player", "music.commands", "music.playlist"]
        if self.number == 1:
            cogs += [
                "moderation.ban", "moderation.kick", "moderation.mute",
                "moderation.timeout", "moderation.lock", "moderation.utility",
                "moderation.games", "moderation.welcome", "moderation.tickets",
                "moderation.tempvoice", "moderation.logs"
            ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                print(f"[COG OK] Bot {self.number} loaded {cog}")
            except Exception as e:
                print(f"[COG ERR] Bot {self.number} {cog}: {e}")

        print(f"Bot {self.number} Cogs loaded.")
        if self.number == 1:
            await self.tree.sync()

    async def on_ready(self):
        print(f"[ONLINE] Bot {self.number} : {self.user}")
        if self.number in bot_states:
            bot_states[self.number]["status"] = "online"
            bot_states[self.number]["name"] = str(self.user)
            bot_states[self.number]["guild_count"] = len(self.guilds)
            if self.voice_id:
                channel = self.get_channel(self.voice_id)
                bot_states[self.number]["voice_channel"] = channel.name if channel else None

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"Music Bot {self.number} 🎵"
            )
        )

        # Connect Lavalink nodes — only Bot 1 creates them; others reuse the shared Pool
        await asyncio.sleep(1)
        try:
            connected = any(
                n.status is NodeStatus.CONNECTED for n in wavelink.Pool.nodes.values()
            )
        except Exception:
            connected = False

        if connected:
            print(f"[LAVALINK] Bot {self.number} reuses existing pool nodes")
            return

        # If a shared node is currently CONNECTING, wait for it instead of duplicating
        for _ in range(10):
            try:
                pending = any(
                    n.status in (NodeStatus.CONNECTING, NodeStatus.CONNECTED)
                    for n in wavelink.Pool.nodes.values()
                )
            except Exception:
                pending = False
            if not pending:
                break
            await asyncio.sleep(1)
        try:
            connected = any(
                n.status is NodeStatus.CONNECTED for n in wavelink.Pool.nodes.values()
            )
        except Exception:
            connected = False
        if connected:
            print(f"[LAVALINK] Bot {self.number} joined existing pool nodes")
            return

        if self.number != 1:
            print(f"[LAVALINK] Bot {self.number} waits for Bot 1 to connect nodes")
            return

        nodes = [
            wavelink.Node(
                uri=cfg["uri"],
                password=cfg["password"],
                retries=3,
                identifier=f"shared-{i}"
            )
            for i, cfg in enumerate(LAVALINK_NODES)
        ]

        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

        ok = sum(1 for n in wavelink.Pool.nodes.values() if n.status is NodeStatus.CONNECTED)
        print(f"[LAVALINK] Bot {self.number} pool nodes connected: {ok}/{len(wavelink.Pool.nodes)}")

        if not ok:
            print(f"[LAVALINK] WARNING: no node connected. Check LAVALINK_NODES env: {LAVALINK_NODES}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if self.number != 1:
            return
        if ctx.command and ctx.command.has_error_handler():
            return
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"⏳ **تمهل!** {error.retry_after:.1f}ث")
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"❌ **استخدم:** `{ctx.prefix}{ctx.command.name} <...>`")
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(f"❌ **ما عندك صلاحية:** {', '.join(error.missing_permissions)}")
        print(f"[CMD ERR] Bot {self.number}: {error}")
        try:
            await ctx.send(f"❌ **{error}**")
        except:
            pass

    async def on_error(self, event, *args, **kwargs):
        print(f"[ERROR] Bot {self.number} event {event}: {traceback.format_exc()}")