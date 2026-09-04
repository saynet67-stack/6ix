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
                "moderation.tempvoice", "moderation.logs", "moderation.trivia",
                "moderation.tictactoe", "moderation.rps", "moderation.help"
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

        # Connect Lavalink nodes - each bot tries independently for better reliability
        await asyncio.sleep(2)
        
        try:
            connected = any(
                n.status is NodeStatus.CONNECTED for n in wavelink.Pool.nodes.values()
            )
        except Exception:
            connected = False

        if connected:
            print(f"[LAVALINK] Bot {self.number} reuses existing pool nodes")
            return

        # Try to connect if no nodes are connected
        print(f"[LAVALINK] Bot {self.number} attempting to connect nodes...")
        
        nodes = [
            wavelink.Node(
                uri=cfg["uri"],
                password=cfg["password"],
                retries=5,
                identifier=f"bot{self.number}-{i}"
            )
            for i, cfg in enumerate(LAVALINK_NODES)
        ]

        try:
            await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=50)
            ok = sum(1 for n in wavelink.Pool.nodes.values() if n.status is NodeStatus.CONNECTED)
            print(f"[LAVALINK] Bot {self.number} pool nodes connected: {ok}/{len(wavelink.Pool.nodes)}")
            
            if not ok:
                print(f"[LAVALINK] WARNING: Bot {self.number} no node connected. Will retry...")
                # Schedule retry
                self.loop.create_task(self._retry_lavalink())
        except Exception as e:
            print(f"[LAVALINK] Bot {self.number} connection failed: {e}")
            self.loop.create_task(self._retry_lavalink())

    async def _retry_lavalink(self):
        """Retry Lavalink connection with exponential backoff"""
        retries = 0
        max_retries = 5
        while retries < max_retries:
            await asyncio.sleep(30 * (2 ** retries))  # Exponential backoff: 30s, 60s, 120s, 240s, 480s
            retries += 1
            
            try:
                connected = any(
                    n.status is NodeStatus.CONNECTED for n in wavelink.Pool.nodes.values()
                )
                if connected:
                    print(f"[LAVALINK] Bot {self.number} already connected, skipping retry")
                    return
                    
                nodes = [
                    wavelink.Node(
                        uri=cfg["uri"],
                        password=cfg["password"],
                        retries=3,
                        identifier=f"bot{self.number}-retry-{retries}"
                    )
                    for i, cfg in enumerate(LAVALINK_NODES)
                ]
                
                await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=50)
                ok = sum(1 for n in wavelink.Pool.nodes.values() if n.status is NodeStatus.CONNECTED)
                print(f"[LAVALINK] Bot {self.number} retry {retries} connected: {ok}/{len(wavelink.Pool.nodes)}")
                
                if ok > 0:
                    return
            except Exception as e:
                print(f"[LAVALINK] Bot {self.number} retry {retries} failed: {e}")
        
        print(f"[LAVALINK] Bot {self.number} gave up after {max_retries} retries")

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
        error_msg = traceback.format_exc()
        print(f"[ERROR] Bot {self.number} event {event}: {error_msg}")
        
        # Log critical errors for debugging
        if "voice" in event.lower() or "lavalink" in event.lower():
            print(f"[CRITICAL] Bot {self.number} {event} error - may affect music playback")
        
        # Attempt recovery for voice-related errors
        if "voice" in event.lower():
            try:
                vc = self.voice_client
                if vc:
                    await vc.disconnect(force=True)
                    print(f"[RECOVERY] Bot {self.number} disconnected from voice due to error")
            except:
                pass