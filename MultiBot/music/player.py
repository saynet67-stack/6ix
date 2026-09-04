import discord
from discord.ext import commands
import wavelink
from wavelink import NodeStatus
import asyncio
import sys
import os
import aiohttp
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LAVALINK_NODES, MUSIC_CHANNEL
from shared_data import update_song, clear_song, format_duration, make_progress_bar

C = 0x2b2d31

class SilenceSource(discord.AudioSource):
    def read(self):
        return b'\x00' * 3840
    def is_opus(self):
        return False

class MusicView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def get_player(self, interaction):
        vc = next(iter(self.cog.bot.voice_clients), None)
        if not vc:
            await interaction.response.send_message("❌ البوت غير متصل", ephemeral=True)
            return None
        return vc

    @discord.ui.button(emoji="⏮", style=discord.ButtonStyle.blurple, row=0)
    async def rewind(self, interaction, button):
        player = await self.get_player(interaction)
        if player and hasattr(player, 'seek'): await player.seek(0)
        await interaction.response.defer()

    @discord.ui.button(emoji="⏸", style=discord.ButtonStyle.gray, row=0)
    async def pause(self, interaction, button):
        player = await self.get_player(interaction)
        if player:
            if hasattr(player, 'pause'): await player.pause(True)
            else: await player.pause()
        await interaction.response.defer()

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.green, row=0)
    async def resume(self, interaction, button):
        player = await self.get_player(interaction)
        if player:
            if hasattr(player, 'resume'): await player.resume()
        await interaction.response.defer()

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.blurple, row=0)
    async def skip(self, interaction, button):
        player = await self.get_player(interaction)
        if player:
            if hasattr(player, 'skip'): await player.skip()
            else: await player.stop()
        await interaction.response.defer()

    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.red, row=0)
    async def stop(self, interaction, button):
        player = await self.get_player(interaction)
        if player:
            if hasattr(player, 'clear_queue'): player.clear_queue()
            if hasattr(player, 'stop'): await player.stop()
            clear_song(self.cog.bot.number)
        await interaction.response.defer()

    @discord.ui.button(emoji="🔉", label="−10", style=discord.ButtonStyle.gray, row=1)
    async def voldown(self, interaction, button):
        player = await self.get_player(interaction)
        if player and hasattr(player, 'set_volume'):
            await player.set_volume(max(player.volume - 10, 10))
        await interaction.response.defer()

    @discord.ui.button(emoji="🔊", label="+10", style=discord.ButtonStyle.gray, row=1)
    async def volup(self, interaction, button):
        player = await self.get_player(interaction)
        if player and hasattr(player, 'set_volume'):
            await player.set_volume(min(player.volume + 10, 150))
        await interaction.response.defer()

class PlayerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoplay = {}
        self.auto_lyrics = {0: False}
        self.last_track = {}
        self.requesters = {}
        self.np_msg = {}
        self.np_channels = {}
        self.np_task = None
        self.lyrics_msg = None
        self.fplayers = {}
        self.lavalink_ready = False
        self._keep_alive_task = None

    async def cog_load(self):
        asyncio.create_task(self._connect_and_keep())
        if self.bot.number == 1:
            asyncio.create_task(self._start_np_loop())

    def get_fplayer(self, guild_id, vc=None):
        if vc and not isinstance(vc, wavelink.Player):
            return None
        if vc:
            self.fplayers[guild_id] = vc
        return self.fplayers.get(guild_id)

    async def _connect_and_keep(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(10)
        
        # Check if voice_id is set
        if not self.bot.voice_id:
            print(f"[24/7] Bot {self.bot.number} no voice_id configured, skipping auto-connect")
            return
        
        channel = self.bot.get_channel(self.bot.voice_id)
        if not channel:
            print(f"[24/7] Bot {self.bot.number} voice channel {self.bot.voice_id} not found, skipping")
            return
        
        # Check if bot has permission to join
        permissions = channel.permissions_for(channel.guild.me)
        if not permissions.connect:
            print(f"[24/7] Bot {self.bot.number} missing CONNECT permission in {channel.name}")
            return
        
        vc = channel.guild.voice_client
        if vc and isinstance(vc, wavelink.Player):
            print(f"[24/7] Bot {self.bot.number} already connected via Lavalink")
            return
        if vc:
            print(f"[24/7] Bot {self.bot.number} already in voice, reconnecting...")
        try:
            await channel.guild.change_voice_state(channel=None)
            await asyncio.sleep(3)
        except:
            pass
        for attempt in range(8):
            if self._lavalink_ready():
                break
            await asyncio.sleep(3)
        if self._lavalink_ready():
            try:
                vc = await channel.connect(cls=wavelink.Player)
                print(f"[24/7] Bot {self.bot.number} connected via Lavalink to {channel.name}")
                return
            except Exception as e:
                print(f"[24/7] Lavalink connect failed: {e}")
        try:
            vc = await channel.connect()
            print(f"[24/7] Bot {self.bot.number} connected to {channel.name}")
            self._keep_alive_task = asyncio.create_task(self._keep_alive(vc))
        except Exception as e:
            print(f"[24/7] Connect failed: {e}")

    def _lavalink_ready(self):
        try:
            return any(n.status is NodeStatus.CONNECTED for n in wavelink.Pool.nodes.values())
        except Exception:
            return False

    async def _keep_alive(self, vc):
        while True:
            await asyncio.sleep(20)
            try:
                if vc and vc.is_connected() and not vc.is_playing():
                    vc.stop()
                    vc.play(SilenceSource())
            except:
                break

    async def build_np_embed(self, player, requester=None):
        track = player.current if hasattr(player, 'current') else None
        if not track: return None
        pos = getattr(player, 'position', 0)
        dur = track.length if hasattr(track, 'length') else 0
        time_str = f"`{format_duration(pos)} / {format_duration(dur)}`"
        desc = f"**{track.title}**"
        if track.author and track.author != "Unknown":
            desc += f"\n{track.author}"
        desc += f"\n\n▸ Duration: {time_str}"
        embed = discord.Embed(color=0xFFFFFF, title="Now Playing", description=desc)
        thumb = getattr(track, "artwork", None) or getattr(track, "thumbnail", None)
        if not thumb and track.uri:
            for p in ("youtu.be/", "watch?v=", "shorts/"):
                if p in track.uri:
                    idx = track.uri.index(p) + len(p)
                    vid = track.uri[idx:idx+11]
                    if len(vid) == 11:
                        thumb = f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                        break
        if thumb: embed.set_image(url=thumb)
        embed.set_footer(text="Not the right song? Try with song and artist name.")
        return embed

    async def update_np(self):
        # تحديث واجهة الأغنية الحالية لكل سيرفر فيه جلسة
        for gid, fp in list(self.fplayers.items()):
            if not fp or not fp.connected or not getattr(fp, 'current', None):
                continue
            track = fp.current
            req = self.requesters.get(gid, "Auto")
            embed = await self.build_np_embed(fp, req)
            if not embed:
                continue
            channel = None
            cid = self.np_channels.get(gid)
            if cid:
                channel = self.bot.get_channel(cid)
            if not channel:
                channel = self.bot.get_channel(MUSIC_CHANNEL)
            if not channel:
                continue
            msg = self.np_msg.get(gid)
            try:
                if msg and msg.channel and msg.channel.id == channel.id:
                    await msg.edit(embed=embed, view=MusicView(self))
                else:
                    msg = await channel.send(embed=embed, view=MusicView(self))
                    self.np_msg[gid] = msg
            except Exception:
                self.np_msg[gid] = None

    async def np_loop(self):
        while True:
            await asyncio.sleep(15)
            try: await self.update_np()
            except: pass

    async def _start_np_loop(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)
        self.np_task = asyncio.create_task(self.np_loop())

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload):
        self.lavalink_ready = True
        print(f"[WAVELINK] Bot {self.bot.number} ready")

    def _sync_lavalink_flag(self):
        self.lavalink_ready = self._lavalink_ready()
        return self.lavalink_ready

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member != self.bot.user: return
        if before.channel and not after.channel:
            await asyncio.sleep(3)
            ch = self.bot.get_channel(self.bot.voice_id)
            if ch:
                try:
                    await ch.connect()
                except: pass

    @commands.command(name="تشغيل_كلمات", aliases=["lyricson", "lyricsoff", "كلمات_تلقائي"])
    async def toggle_auto_lyrics(self, ctx):
        await ctx.defer() if hasattr(ctx, 'interaction') and ctx.interaction else None
        gid = ctx.guild.id
        if not self.auto_lyrics.get(gid, False):
            self.auto_lyrics[gid] = True
            await ctx.send("✅ Auto‑lyrics **ON**")
        else:
            self.auto_lyrics[gid] = False
            await ctx.send("❌ Auto‑lyrics **OFF**")

async def setup(bot):
    await bot.add_cog(PlayerCog(bot))