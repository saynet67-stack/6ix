import discord
from discord.ext import commands
from gtts import gTTS
import io
import asyncio
import subprocess

C = 0x2b2d31
TARGET_IDS = [587979710059905024, 843515767324672021]

HAVE_FFMPEG = False
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    HAVE_FFMPEG = True
except:
    pass

class TTSHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._tts_lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return
        if member.id not in TARGET_IDS: return
        if not after.channel: return
        if before.channel == after.channel: return
        if self._tts_lock.locked(): return
        async with self._tts_lock:
            await self._say_hi(member, after.channel)

    async def _say_hi(self, member, channel):
        if not HAVE_FFMPEG: return
        player = channel.guild.voice_client
        if not player or not player.channel or player.channel.id != channel.id: return
        try:
            tts = gTTS(text="Hi Maden", lang="en", slow=False)
            fp = io.BytesIO()
            tts.write_to_fp(fp); fp.seek(0)
        except Exception as e:
            print(f"[TTS] gen: {e}"); return
        try:
            import wavelink
            is_lavalink = isinstance(player, wavelink.Player)
            was_playing = False; saved_track = None; saved_pos = 0
            pcog = self.bot.get_cog("PlayerCog")
            if is_lavalink:
                was_playing = player.playing
                saved_track = player.current if was_playing else None
                saved_pos = player.position if was_playing else 0
                if was_playing: await player.pause(True); await asyncio.sleep(0.3)
                await player.disconnect(force=True); await asyncio.sleep(0.5)
            else:
                if player and (player.is_playing() if hasattr(player, 'is_playing') else False):
                    player.stop()
            tmp = await channel.connect()
            def after_tts(err):
                asyncio.run_coroutine_threadsafe(
                    self._after_tts(channel, tmp, is_lavalink, was_playing, saved_track, saved_pos, pcog),
                    self.bot.loop)
            source = discord.FFmpegPCMAudio(fp, pipe=True)
            tmp.play(source, after=after_tts)
        except Exception as e:
            print(f"[TTS] playback: {e}")

    async def _after_tts(self, channel, tmp, is_lavalink, was_playing, saved_track, saved_pos, pcog):
        await asyncio.sleep(0.5)
        try: await tmp.disconnect(force=True)
        except: pass
        if was_playing and saved_track:
            await asyncio.sleep(1)
            try:
                if is_lavalink:
                    import wavelink
                    new_player = await channel.connect(cls=wavelink.Player)
                    await new_player.play(saved_track, start_time=saved_pos)
                    print(f"[TTS] resumed wavelink at {saved_pos}ms")
            except: pass

async def setup(bot):
    await bot.add_cog(TTSHandler(bot))
