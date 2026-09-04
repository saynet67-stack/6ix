import discord
from discord.ext import commands
from discord import app_commands
import wavelink
import sys
import os
import random
import math
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MUSIC_CHANNEL
from shared_data import update_song, format_duration

C = 0x2b2d31

class MusicControlView(discord.ui.View):
    def __init__(self, cog, player, is_wl):
        super().__init__(timeout=None)
        self.cog = cog
        self.player = player
        self.is_wl = is_wl
        self.stop_btn = discord.ui.Button(label="Stop", style=discord.ButtonStyle.red, row=0)
        self.stop_btn.callback = self.stop_cb; self.add_item(self.stop_btn)
        self.loop_btn = discord.ui.Button(label="Loop", style=discord.ButtonStyle.gray, row=0)
        self.loop_btn.callback = self.loop_cb; self.add_item(self.loop_btn)
        self.skip_btn = discord.ui.Button(label="Skip", style=discord.ButtonStyle.gray, row=0)
        self.skip_btn.callback = self.skip_cb; self.add_item(self.skip_btn)
        self.pp_btn = discord.ui.Button(label="Pause", style=discord.ButtonStyle.gray, row=0)
        self.pp_btn.callback = self.pp_cb; self.add_item(self.pp_btn)
        self.prev_btn = discord.ui.Button(label="Previous", style=discord.ButtonStyle.gray, row=0)
        self.prev_btn.callback = self.prev_cb; self.add_item(self.prev_btn)

    def _owns_vc(self, interaction):
        if not interaction.user.voice: return False
        return interaction.user.voice.channel.id == self.cog.bot.voice_id

    async def stop_cb(self, interaction):
        if not self._owns_vc(interaction):
            return await interaction.response.send_message("❌ مش أمرك", ephemeral=True)
        await interaction.response.defer()
        if self.is_wl: self.player.queue.clear(); await self.player.stop()
        else: self.player.clear_queue(); await self.player.stop()
        from shared_data import clear_song
        clear_song(self.cog.bot.number)
        try: await interaction.message.delete()
        except: pass

    async def loop_cb(self, interaction):
        if not self._owns_vc(interaction):
            return await interaction.response.send_message("❌ مش أمرك", ephemeral=True)
        gid = interaction.guild_id
        cur = self.cog.loops.get(gid)
        if cur == "track": self.cog.loops[gid] = "queue"; await interaction.response.send_message("🔁 Queue Loop", ephemeral=True)
        elif cur == "queue": self.cog.loops[gid] = None; await interaction.response.send_message("▶️ Loop Off", ephemeral=True)
        else: self.cog.loops[gid] = "track"; await interaction.response.send_message("🔂 Track Loop", ephemeral=True)

    async def skip_cb(self, interaction):
        if not self._owns_vc(interaction):
            return await interaction.response.send_message("❌ مش أمرك", ephemeral=True)
        await interaction.response.defer()
        if self.is_wl: await self.player.stop()
        else: await self.player.skip()

    async def pp_cb(self, interaction):
        if not self._owns_vc(interaction):
            return await interaction.response.send_message("❌ مش أمرك", ephemeral=True)
        await interaction.response.defer()
        if self.is_wl:
            if self.player.playing: await self.player.pause(True)
            else: await self.player.pause(False)
        else:
            if self.player.playing: await self.player.pause()
            else: await self.player.resume()

    async def prev_cb(self, interaction):
        if not self._owns_vc(interaction):
            return await interaction.response.send_message("❌ مش أمرك", ephemeral=True)
        await interaction.response.defer()
        if self.is_wl and hasattr(self.player, 'seek'): await self.player.seek(0)
        else: await self.player.skip()

class MusicCommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loops = {}

    async def check_channel(self, ctx):
        return True

    async def voice_check(self, ctx, silent=False):
        if not ctx.author.voice:
            if self.bot.number == 1 and not silent:
                await ctx.send(embed=self.premium_embed("❌ **لازم تكون في روم صوتي**"))
            return False
        user_room = ctx.author.voice.channel.id
        if self.bot.voice_id == user_room:
            return True
        vc = ctx.voice_client
        if vc and vc.channel and vc.channel.id == user_room:
            return True
        from shared_data import all_bots
        assigned = any(b.voice_id == user_room for b in all_bots)
        if not assigned and self.bot.number == 1:
            return True
        return False

    def get_pcog(self):
        return self.bot.get_cog("PlayerCog")

    async def _get_player(self, ctx):
        pcog = self.get_pcog()
        if not pcog: return None, False
        if pcog._sync_lavalink_flag():
            p = ctx.voice_client
            if p and isinstance(p, wavelink.Player) and hasattr(p, 'playing'):
                return p, True
            if p: return p, True
        gid = ctx.guild.id
        fp = pcog.fplayers.get(gid)
        if fp and isinstance(fp, wavelink.Player) and fp.connected:
            return fp, True
        vc = ctx.voice_client
        if vc and isinstance(vc, wavelink.Player):
            pcog.get_fplayer(gid, vc)
            return vc, True
        return None, False

    def premium_embed(self, desc=None, title=None, thumb=None, image=None, footer=None):
        e = discord.Embed(color=C, title=title, description=desc)
        if thumb: e.set_thumbnail(url=thumb)
        if image: e.set_image(url=image)
        if footer: e.set_footer(text=footer)
        return e

    def make_progress(self, pos, duration, length=20):
        if not duration: return "▬" * length
        ratio = pos / duration
        filled = round(ratio * length)
        return "▬" * filled + "🔘" + "─" * (length - filled - 1) if filled < length else "▬" * length

    @commands.command(name="ش", aliases=["شغل"])
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def play(self, ctx, *, query):
        try:
            if not await self.check_channel(ctx): return
            if not await self.voice_check(ctx): return

            pcog = self.get_pcog()
            if not pcog:
                return await ctx.send(embed=self.premium_embed("❌ **مشغل الموسيقى مش متاح**"))

            if not pcog._sync_lavalink_flag():
                return await ctx.send(embed=self.premium_embed("❌ **Lavalink غير متاح - يرجى الاتصال بالمسؤول**"))

            vc = await self._ensure_user_room(ctx)
            if not vc:
                return await ctx.send(embed=self.premium_embed("❌ **تعذر الاتصال بالروم الصوتي**"))

            # التشغيل مع إظهار الخطأ الحقيقي
            try:
                await self._lavalink_play(ctx, query, pcog, vc)
            except Exception as e:
                print(f"[PLAY ERROR] {e}")
                if self.bot.number == 1:
                    await ctx.send(embed=self.premium_embed(f"❌ **حصل خطأ أثناء التشغيل:**\n`{e}`"))

        except Exception as e:
            await ctx.send(embed=self.premium_embed(f"❌ **خطأ:** {e}"))
            print(f"[PLAY ERR] {e}")

    async def _ensure_wl_player(self, ctx):
        vc = ctx.voice_client
        if vc and isinstance(vc, wavelink.Player):
            return vc
        if vc:
            print(f"[WL] existing regular VC, upgrading to Lavalink...")
            try:
                await ctx.guild.change_voice_state(channel=None)
                await asyncio.sleep(2)
            except:
                pass
        channel = ctx.author.voice.channel if ctx.author.voice else ctx.bot.get_channel(ctx.bot.voice_id)
        if not channel:
            return None
        try:
            return await channel.connect(cls=wavelink.Player)
        except Exception as e:
            print(f"[WL] connect err: {e}")
            return None

    async def _ensure_user_room(self, ctx):
        user_ch = ctx.author.voice.channel if ctx.author.voice else None
        if not user_ch:
            return None
        vc = ctx.voice_client
        if vc and isinstance(vc, wavelink.Player) and vc.channel and vc.channel.id == user_ch.id:
            return vc
        if vc:
            try:
                await vc.disconnect(force=True)
                await asyncio.sleep(1)
            except:
                pass
        try:
            return await user_ch.connect(cls=wavelink.Player)
        except Exception as e:
            print(f"[WL] join user room err: {e}")
            return None

    @app_commands.command(name="play", description="شغل أغنية أو playlist")
    async def slash_play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer(thinking=True)
        if not interaction.user.voice:
            return await interaction.followup.send("ادخل voice channel أولاً!")
        channel = interaction.user.voice.channel
        player = channel.guild.voice_client
        if player and not isinstance(player, wavelink.Player):
            try:
                await channel.guild.change_voice_state(channel=None)
                await asyncio.sleep(2)
                player = None
            except:
                pass
        if not player:
            try:
                player = await channel.connect(cls=wavelink.Player)
            except Exception as e:
                return await interaction.followup.send(f"تعذر الاتصال: {e}")
        from music.dj import search_one
        track = await search_one(query)
        if not track:
            return await interaction.followup.send("ما لقيتش نتايج 😔")
        if player.playing:
            await player.queue.put_wait(track)
            return await interaction.followup.send(f"📌 تمت الإضافة: **{track.title}**")
        await player.play(track)
        try: player.autoplay = wavelink.AutoPlayMode.partial
        except: pass
        embed = discord.Embed(title="▶️ جاري التشغيل",
            description=f"**{track.title}**\n{track.author}\n{track.uri}",
            color=0x00ff00)
        await interaction.followup.send(embed=embed)

    async def _lavalink_play(self, ctx, query, pcog, vc=None):
        if not vc or not isinstance(vc, wavelink.Player):
            vc = await self._ensure_user_room(ctx)
            if not vc:
                return await ctx.send(embed=self.premium_embed("❌ **تعذر الاتصال بالروم الصوتي**"))
        try:
            tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTubeMusic)
        except Exception as e:
            print(f"[LAVALINK] YouTubeMusic search failed: {e}")
            try:
                tracks = await wavelink.Playable.search(query)
            except Exception as e2:
                print(f"[LAVALINK] Default search failed: {e2}")
                return await ctx.send(embed=self.premium_embed("❌ **فشل البحث - حاول مرة أخرى**"))
        if not tracks:
            return await ctx.send(embed=self.premium_embed("❌ **ما لقيت نتيجة للبحث**"))
        track = tracks[0]
        await self._play_track_wl(ctx, track, pcog, vc)

    async def _yt_thumb(self, uri):
        if not uri: return None
        for p in ("youtu.be/", "watch?v=", "shorts/"):
            if p in uri:
                idx = uri.index(p) + len(p)
                v = uri[idx:idx+11]
                if len(v)==11: return f"https://img.youtube.com/vi/{v}/hqdefault.jpg"
        return None

    def _track_embed(self, track, player, prefix="Now Playing"):
        from datetime import datetime
        dur = format_duration(track.length)
        
        # الحصول على loop icon من player
        loop_icon = ""
        if hasattr(player, 'loop'):
            if player.loop == 'track':
                loop_icon = "🔂"
            elif player.loop == 'queue':
                loop_icon = "🔁"
        
        # الوقت الحالي
        current_time = datetime.now().strftime("%-I:%M %p")
        
        # تصميم أفضل للوصف
        desc = f"🎵 **{track.title}**"
        if track.author and track.author != "Unknown":
            desc += f"\n👤 **{track.author}**"
        desc += f"\n\n⏱️ **Duration:** `{dur}` {loop_icon}"
        
        thumb = getattr(track, "artwork", None) or getattr(track, "thumbnail", None) or self._yt_thumb(track.uri)
        e = discord.Embed(color=0x3ba55c, title=f"🎶 {prefix}", description=desc)
        if thumb: e.set_thumbnail(url=thumb)
        
        # إضافة الوقت في الفوتر
        e.set_footer(text=f"— {current_time} | Music Bot")
        
        # إضافة طالب الأغنية إذا كان متاح
        pcog = self.bot.get_cog("PlayerCog")
        if pcog:
            guild_id = getattr(self.bot.guilds[0], 'id', 0) if self.bot.guilds else 0
            requester = pcog.requesters.get(guild_id)
            if requester:
                e.add_field(name="🎤 Requested by", value=f"@{requester.name}", inline=False)
        
        return e

    async def _show_lyrics_for(self, ctx, track, pcog, player):
        await asyncio.sleep(5)
        if pcog and pcog.auto_lyrics.get(ctx.guild.id, False):
            ch = ctx.channel
            try:
                lyrics = await pcog.fetch_lyrics(track.author, track.title)
                if lyrics:
                    lines = [l for l in lyrics.split("\n") if l.strip()]
                    if len(lines) >= 2:
                        desc = "\n".join(lines[:25])[:3500]
                        embed = discord.Embed(color=C, title=f"🎤 {track.title}", description=desc)
                        await ch.send(embed=embed)
            except: pass

    async def _play_track_wl(self, ctx, track, pcog, player=None):
        pcog.requesters[ctx.guild.id] = ctx.author

        if not player or not isinstance(player, wavelink.Player):
            player = ctx.voice_client

        if not player or not isinstance(player, wavelink.Player):
            print(f"[WL] voice client not wavelink.Player, upgrading")
            player = await self._ensure_user_room(ctx)

        if not player or not isinstance(player, wavelink.Player):
            return await ctx.send(embed=self.premium_embed("❌ **تعذر تشغيل Lavalink**"))

        await player.set_volume(100)

        try:
            if player.playing:
                await player.queue.put_wait(track)
                pos = self._qsize(player)
                embed = self._track_embed(track, player, f"📌 Added #{pos}" if pos else "📌 Added")
                if self.bot.number == 1:
                    await ctx.send(embed=embed)
            else:
                await player.queue.put_wait(track)
                await player.play(player.queue.get())
                print(f"[PLAY SUCCESS] {track.title}")
                try:
                    player.autoplay = wavelink.AutoPlayMode.partial
                except:
                    pass

                if ctx.channel.id != MUSIC_CHANNEL and self.bot.number == 1:
                    embed = self._track_embed(track, player, "▶ Now Playing")
                    view = MusicControlView(self, player, True)
                    await ctx.send(embed=embed, view=view)
                    pcog.np_channels[ctx.guild.id] = ctx.channel.id

                asyncio.create_task(self._show_lyrics_for(ctx, track, pcog, player))

        except Exception as e:
            print(f"[PLAY FAILED] {track.title} -> {e}")
            raise e

    def _qsize(self, player):
        try:
            if hasattr(player, 'queue') and player.queue is not None:
                q = player.queue
                if hasattr(q, 'count'): return q.count
                if hasattr(q, 'qsize'): return q.qsize()
                if hasattr(q, '__len__'): return len(q)
        except: pass
        return 0

    @play.error
    async def play_error(self, ctx, error):
        if self.bot.number != 1: return
        if isinstance(error, commands.CommandOnCooldown):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self.premium_embed("❌ **استخدم:** `ش <اسم الأغنية>`"))

    @commands.command(name="وقف")
    async def pause(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl: await fp.pause(True)
        else: await fp.pause()
        await ctx.send(embed=self.premium_embed("⏸️ **Paused** — استخدم `كمل` للاستئناف"))

    @commands.command(name="كمل", aliases=["زود"])
    async def resume(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl: await fp.pause(False)
        else: await fp.resume()
        await ctx.send(embed=self.premium_embed("▶️ **Resumed**"))

    @commands.command(name="س", aliases=["سكيب", "سكب", "تخطي"])
    async def skip(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        loop = self.loops.get(ctx.guild.id)
        if loop == "track":
            fp, is_wl = await self._get_player(ctx)
            if fp:
                if is_wl and hasattr(fp, 'seek'):
                    await fp.seek(0); await fp.play(fp.current, start_time=0)
                elif hasattr(fp, 'skip'): await fp.skip()
            return await ctx.send(embed=self.premium_embed("🔂 **Track looped**"))
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl: await fp.stop()
        elif hasattr(fp, 'skip'): await fp.skip()
        if self.bot.number == 1:
            await ctx.send(embed=self.premium_embed("⏭️ **Skipped**"))

    @commands.command(name="ايقاف", aliases=["iqaaf"])
    async def stop(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if fp:
            if is_wl: fp.queue.clear(); await fp.stop()
            else: fp.stop()
        from shared_data import clear_song
        clear_song(self.bot.number)
        await ctx.send(embed=self.premium_embed("⏹️ **Stopped** — تم مسح القائمة"))

    @commands.command(name="ترك")
    async def leave(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            from shared_data import clear_song
            clear_song(self.bot.number)
            await ctx.send(embed=self.premium_embed("👋 **Disconnected**"))

    @commands.command(name="كرر", aliases=["loop", "تكرار"])
    async def toggle_loop(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        gid = ctx.guild.id
        cur = self.loops.get(gid)
        if cur == "track": self.loops[gid] = "queue"; await ctx.send(embed=self.premium_embed("🔁 **Queue Loop**"))
        elif cur == "queue": self.loops[gid] = None; await ctx.send(embed=self.premium_embed("▶️ **Loop Off**"))
        else: self.loops[gid] = "track"; await ctx.send(embed=self.premium_embed("🔂 **Track Loop**"))

    @commands.command(name="خلط", aliases=["shuffle", "قلب"])
    async def shuffle(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl:
            if fp.queue.is_empty: return await ctx.send(embed=self.premium_embed("❌ **القائمة فاضية**"))
            q = list(fp.queue); random.shuffle(q); fp.queue.clear()
            for t in q: await fp.queue.put_wait(t)
        else:
            if not fp.queue: return await ctx.send(embed=self.premium_embed("❌ **القائمة فاضية**"))
            random.shuffle(fp.queue)
        await ctx.send(embed=self.premium_embed(f"🔀 **Shuffled**"))

    @commands.command(name="حذف", aliases=["remove", "مسح_أغنية"])
    async def remove(self, ctx, position: int):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl:
            if fp.queue.is_empty: return await ctx.send(embed=self.premium_embed("❌ **القائمة فاضية**"))
            q = list(fp.queue)
            if position < 1 or position > len(q): return await ctx.send(embed=self.premium_embed(f"❌ **الرقم من 1 إلى {len(q)}**"))
            removed = q.pop(position - 1); fp.queue.clear()
            for t in q: await fp.queue.put_wait(t)
        else:
            if not fp.queue: return await ctx.send(embed=self.premium_embed("❌ **القائمة فاضية**"))
            if position < 1 or position > len(fp.queue): return await ctx.send(embed=self.premium_embed(f"❌ **الرقم من 1 إلى {len(fp.queue)}**"))
            removed = fp.queue.pop(position - 1)
        await ctx.send(embed=self.premium_embed(f"🗑️ **Removed**"))

    @commands.command(name="اقفز", aliases=["jump", "اذهب_إلى"])
    async def jump(self, ctx, position: int):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return
        if is_wl:
            if fp.queue.is_empty: return await ctx.send(embed=self.premium_embed("❌ **القائمة فاضية**"))
            q = list(fp.queue)
            if position < 1 or position > len(q): return await ctx.send(embed=self.premium_embed(f"❌ **الرقم من 1 إلى {len(q)}**"))
            track = q[position - 1]; new_q = q[position - 1:]; fp.queue.clear()
            for t in new_q: await fp.queue.put_wait(t)
            await fp.stop()
        else:
            await fp.stop()
        await ctx.send(embed=self.premium_embed(f"⏭️ **Jumped to #{position}**"))

    @commands.command(name="الان", aliases=["np", "حاليا"])
    async def nowplaying(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
        if is_wl:
            if not fp.playing: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
            track = fp.current; pos = fp.position; dur = track.length
            title = track.title; uri = track.uri; author = track.author
            thumb = getattr(track, "artwork", None) or getattr(track, "thumbnail", None)
            vol = fp.volume; qsize = len(fp.queue)
        else:
            if not fp.current: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
            track = fp.current
            if not fp.playing: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
            dur = track.length; pos = fp.position
            title = track.title; uri = track.uri; author = track.author
            thumb = getattr(track, "artwork", None); vol = f"{fp.volume}%" if hasattr(fp, 'volume') else "100%"
            qsize = len(fp.queue) if hasattr(fp, 'queue') else 0
        pct = round(pos / dur * 100, 1) if dur else 0
        bar = self.make_progress(pos, dur)
        loop_icon = {"track": "🔂", "queue": "🔁"}.get(self.loops.get(ctx.guild.id), "▶️")
        embed = self.premium_embed(f"[**{title}**]({uri})\n{author}\n\n{bar}  `{format_duration(pos)} / {format_duration(dur)}`", thumb=thumb, footer=f"Vol: {vol} | {loop_icon} | Bot {self.bot.number}")
        await ctx.send(embed=embed)

    @commands.command(name="ق", aliases=["list", "قائمة"])
    async def queue(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return await ctx.send(embed=self.premium_embed("❌ **البوت غير متصل**"))
        if is_wl:
            if fp.queue.is_empty: return await ctx.send(embed=self.premium_embed("📭 **القائمة فاضية**"))
            qlist = list(fp.queue); total_dur = sum(t.length for t in qlist)
            embed = discord.Embed(color=C, title=f"📋 Queue • {len(qlist)} أغاني")
            for i, t in enumerate(qlist[:50], 1):
                embed.add_field(name=f"`#{i:02d}` {t.title[:50]}", value=f"{t.author} ⏱ {format_duration(t.length)}", inline=False)
            embed.set_footer(text=f"⏱ {format_duration(total_dur)} • Bot {self.bot.number}")
            await ctx.send(embed=embed)
        else:
            q = fp.queue if hasattr(fp, 'queue') else []
            if not q: return await ctx.send(embed=self.premium_embed("📭 **القائمة فاضية**"))
            total_dur = sum(t.length for t in q) if hasattr(q[0], 'length') else 0
            embed = discord.Embed(color=C, title=f"📋 Queue • {len(q)} أغاني")
            for i, t in enumerate(q[:50], 1):
                embed.add_field(name=f"`#{i:02d}` {t.title[:50]}", value=f"{t.author} ⏱ {format_duration(t.length)}", inline=False)
            embed.set_footer(text=f"⏱ {format_duration(total_dur)} • Bot {self.bot.number}")
            await ctx.send(embed=embed)

    @commands.command(name="كلمات", aliases=["lyrics", "ك"])
    async def lyrics(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
        if is_wl:
            if not fp.playing or not fp.current: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
            track = fp.current
        else:
            if not fp.current: return await ctx.send(embed=self.premium_embed("❌ **مافيش أغنية شغالة**"))
            track = fp.current
        await ctx.send(embed=self.premium_embed(f"🔍 **بحث عن كلمات** `{track.title[:50]}`..."))
        pcog = self.get_pcog()
        if pcog:
            lyrics = await pcog.fetch_lyrics(track.author, track.title)
            if lyrics:
                for j, chunk in enumerate([lyrics[i:i+1900] for i in range(0, len(lyrics), 1900)][:5]):
                    await ctx.send(embed=discord.Embed(color=C, title=f"🎤 {track.title}" if j == 0 else None, description=chunk))
                return
        await ctx.send(embed=self.premium_embed("❌ **ما لقيت كلمات**"))

    @commands.command(name="صوت", aliases=["volume", "vol", "ح"])
    async def set_volume(self, ctx, level: int = None):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        fp, is_wl = await self._get_player(ctx)
        if not fp: return await ctx.send(embed=self.premium_embed("❌ **البوت غير متصل**"))
        if is_wl: cur_vol = fp.volume
        else: cur_vol = getattr(fp, 'volume', 100)
        if level is None:
            bar = "🔊 " + "█" * round(cur_vol / 10) + "░" * (15 - round(cur_vol / 10))
            return await ctx.send(embed=self.premium_embed(f"{bar}  **{cur_vol}%**"))
        if level < 1 or level > 150: return await ctx.send(embed=self.premium_embed("❌ **من 1 إلى 150**"))
        if is_wl: await fp.set_volume(level)
        else: fp.volume = level
        bar = "🔊 " + "█" * round(level / 10) + "░" * (15 - round(level / 10))
        await ctx.send(embed=self.premium_embed(f"{bar}  **{level}%**"))

    @commands.command(name="تلقائي")
    async def toggle_autoplay(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        pcog = self.get_pcog()
        if not pcog: return
        gid = ctx.guild.id
        pcog.autoplay[gid] = not pcog.autoplay.get(gid, False)
        state = "🟢 ON" if pcog.autoplay[gid] else "🔴 OFF"
        await ctx.send(embed=self.premium_embed(f"🎵 **Autoplay** {state}"))

    @commands.command(name="دائم", aliases=["24h", "24/7"])
    async def toggle_247(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        await ctx.send(embed=self.premium_embed("⏳ **24/7 Mode**"))

    @commands.command(name="عشوائي", aliases=["random", "mix", "ميكس"])
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def random_song(self, ctx, *, query: str = None):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        pcog = self.get_pcog()
        if not pcog: return
        if not pcog._sync_lavalink_flag():
            return await ctx.send(embed=self.premium_embed("❌ **Lavalink غير متاح**"))
        return await self._random_lavalink(ctx, query, pcog)

    async def _random_lavalink(self, ctx, query, pcog):
        last = pcog.last_track.get(ctx.guild.id)
        search = query or (f"{last.title} {last.author} mix" if last else "trending music mix")
        from music.dj import search_many
        try: tracks = await search_many(search, 10)
        except: return await ctx.send(embed=self.premium_embed("❌ **خطأ في البحث**"))
        if not tracks: return await ctx.send(embed=self.premium_embed("❌ **ما لقيت نتائج**"))
        random.shuffle(tracks)
        player = ctx.voice_client
        if not player or not isinstance(player, wavelink.Player):
            player = await self._ensure_user_room(ctx)
            if not player:
                return await ctx.send(embed=self.premium_embed("❌ **البوت غير متصل wavelink**"))
        await player.set_volume(100)
        pcog.requesters[ctx.guild.id] = ctx.author
        for t in tracks[:10]: await player.queue.put_wait(t)
        if not player.playing: await player.play(player.queue.get())
        await ctx.send(embed=self.premium_embed(f"✅ **{min(10, len(tracks))}** أغاني مضافة", title="🎲 Random Mix"))

    @commands.command(name="طلب", aliases=["request", "req"])
    @commands.cooldown(1, 8, commands.BucketType.user)
    async def request_song(self, ctx, *, query):
        if not ctx.author.voice: return await ctx.send(embed=self.premium_embed("❌ **لازم تكون في روم صوتي**"))
        pcog = self.get_pcog()
        if not pcog: return
        from music.dj import search_one
        track = await search_one(query)
        if not track:
            return await ctx.send(embed=self.premium_embed("❌ **ما لقيت نتيجة**"))
        player = await self._ensure_user_room(ctx)
        if not player:
            return await ctx.send(embed=self.premium_embed("❌ **تعذر الاتصال بالروم الصوتي**"))
        pcog.requesters[ctx.guild.id] = ctx.author
        if player.playing:
            await player.queue.put_wait(track)
        else:
            await player.play(track)
        await ctx.send(embed=self.premium_embed(f"[**{track.title}**]({track.uri})\n{track.author} • {format_duration(track.length)}", title="📩 Request", thumb=getattr(track, "artwork", None) or getattr(track, "thumbnail", None), footer=f"{ctx.author.display_name} • Bot {self.bot.number}"))

    @commands.command(name="حالة")
    async def status(self, ctx):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx, silent=True): return
        fp, is_wl = await self._get_player(ctx)
        vc_name = "غير متصل"; vol = "—"; playing = "—"
        if fp:
            ch = self.bot.get_channel(self.bot.voice_id)
            vc_name = f"#{ch.name}" if ch else "?"
            if is_wl:
                vol = f"{fp.volume}%"
                playing = f"[{fp.current.title[:30]}]({fp.current.uri})" if fp.playing and fp.current else "متوقف"
            else:
                vol = f"{getattr(fp, 'volume', 100)}%"
                playing = f"[{fp.current.title[:30]}]({fp.current.uri})" if fp.current else "متوقف"
        embed = discord.Embed(color=C, title=f"🤖 Bot {self.bot.number} — الحالة")
        embed.add_field(name="📡 الحالة", value="🟢 متصل", inline=True)
        embed.add_field(name="🎧 الروم", value=vc_name, inline=True)
        embed.add_field(name="🔊 الصوت", value=vol, inline=True)
        if playing != "—": embed.add_field(name="🎵 شغال", value=playing, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="لوحة")
    async def panel(self, ctx):
        if not await self.check_channel(ctx): return
        if self.bot.number != 1: return
        embed = discord.Embed(color=C, title="🎛️ لوحة التحكم",
            description="**🎶 الأوامر:**\n`ش` تشغيل • `الان` الأغنية الحالية • `ق` القائمة\n`س` تخطي • `وقف`/`كمل`/`اقفل` • `صوت` 🔊\n`كرر` 🔂 • `خلط` 🔀 • `حذف` 🗑️\n`طلب` أطلب من اي شات • `عشوائي` 🎲\n`دائم` ⏳ 24/7 • `كلمات` 📝\n\n**🛡️ الإدارة (Bot 1):**\n`يكسمك` 🚫 • `برا` 👋 • `اكتم` 🔇\n`تايم` ⏰ • `فك` 🔓 • `مسح` 🧹\n`اسم` تغيير اسم • `اشتم` / `يلعن` • `اسحب` + منشن\n\n**🎮 لعبة:**\n`لعبه` 🎲")
        await ctx.send(embed=embed)

    @commands.command(name="مساعدة", aliases=["اوامر", "الأوامر", "commands", "help"])
    async def help_cmd(self, ctx):
        if self.bot.number != 1: return
        if not await self.check_channel(ctx): return
        labels = {"MusicCommandsCog": "🎶 Music", "PlayerCog": "🎶 Player", "PlaylistCog": "🎵 Playlist", "BanCog": "🚫 Ban", "KickCog": "👋 Kick", "MuteCog": "🔇 Mute", "TimeoutCog": "⏰ Timeout", "LockCog": "🔒 Lock", "UtilityCog": "🛡️ Utility", "TempVoice": "🎤 Temp Voice", "GamesCog": "🎮 Games", "WelcomeCog": "👋 Welcome", "TicketsCog": "🎫 Tickets"}

        items = []
        for name, cmd in self.bot.all_commands.items():
            if getattr(cmd, "parent", None):
                continue
            if isinstance(cmd, commands.Group):
                subs = list(getattr(cmd, "all_commands", {}) or {})
                if subs:
                    for s in subs:
                        items.append(f"`{name} {s}`")
                else:
                    items.append(f"`{name}`")
            else:
                items.append(f"`{name}`")

        items = sorted(set(items))
        pages = []
        current = []
        size = 0
        MAX_SIZE = 5800
        for it in items:
            if current and size + len(it) + 1 > MAX_SIZE:
                pages.append(current)
                current = []
                size = 0
            current.append(it)
            size += len(it) + 1
        if current:
            pages.append(current)

        total = len(pages)
        for pi, page in enumerate(pages):
            embed = discord.Embed(color=C, title="📋 كل أوامر البوت")
            for i in range(0, len(page), 12):
                embed.add_field(name="▪️", value="\n".join(page[i:i+12]), inline=True)
            embed.set_footer(text=f"{self.bot.user.name} • صفحة {pi+1}/{total} • اكتب `مساعدة` في أي وقت")
            await ctx.send(embed=embed)

    @commands.command(name="تشخيص")
    async def diagnose(self, ctx):
        if not await self.check_channel(ctx): return
        if self.bot.number != 1: return
        pcog = self.get_pcog()
        lavalink_ok = pcog._sync_lavalink_flag() if pcog else False
        fp, is_wl = await self._get_player(ctx)
        embed = discord.Embed(color=C, title="🔧 Diagnostics")
        embed.add_field(name="Bots Online", value=str(len([b for b in [self.bot]])))
        embed.add_field(name="Mode", value="⚡ Lavalink" if lavalink_ok else "🎧 yt-dlp", inline=True)
        if fp:
            embed.add_field(name="🔊 Voice", value="✅ Connected", inline=True)
            embed.add_field(name="▶️ Playing", value="✅ Yes" if (is_wl and fp.playing) or (not is_wl and fp.current) else "❌ No", inline=True)
            embed.add_field(name="🔊 Volume", value=f"{fp.volume if is_wl else getattr(fp, 'volume', 100)}%", inline=True)
        else:
            embed.add_field(name="🔊 Player", value="❌ Not connected", inline=False)
        embed.set_footer(text="yt-dlp is the DEFAULT — Lavalink is optional")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicCommandsCog(bot))
