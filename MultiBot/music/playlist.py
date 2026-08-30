import json
import os
import asyncio
import wavelink
import discord
from discord.ext import commands
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PLAYLIST_FILE = "playlists.json"

def load_playlists():
    if not os.path.exists(PLAYLIST_FILE):
        return {}
    try:
        with open(PLAYLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_playlists(data):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class PlaylistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def check_channel(self, ctx):
        return True

    async def voice_check(self, ctx, silent=False):
        return bool(ctx.author.voice)

    @commands.command(name="بلاي ليست", aliases=["playlist", "بلاي"])
    async def list_playlists(self, ctx):
        if not await self.check_channel(ctx): return
        data = load_playlists()
        guild_id = str(ctx.guild.id)
        user_lists = data.get(guild_id, {})
        if not user_lists:
            return await ctx.send(embed=discord.Embed(description="ما عندك أي بلاي ليست محفوظة.\nاستخدم `احفظ <اسم>` لحفظ الأغاني.", color=0x2b2d31))
        embed = discord.Embed(title="📋 البلاي ليست", color=0x2b2d31)
        for name, tracks in user_lists.items():
            total = len(tracks)
            first = tracks[0]["title"] if tracks else ""
            embed.add_field(name=f"🎵 {name}", value=f"{total} أغنية\n`{first[:40]}`", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="احفظ", aliases=["save"])
    async def save_playlist(self, ctx, *, name):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        player_cog = self.bot.get_cog("PlayerCog")
        if not player_cog: return
        vc = ctx.voice_client
        if not vc or not isinstance(vc, wavelink.Player) or not getattr(vc, "queue", None) or not vc.queue:
            return await ctx.send("❌ القائمة فارغة")

        data = load_playlists()
        guild_id = str(ctx.guild.id)
        if guild_id not in data:
            data[guild_id] = {}

        tracks = []
        for t in list(vc.queue):
            tracks.append({
                "title": t.title,
                "author": t.author,
                "uri": t.uri
            })
        data[guild_id][name] = tracks
        save_playlists(data)
        await ctx.send(embed=discord.Embed(description=f"✅ تم حفظ **{len(tracks)}** أغنية في `{name}`", color=0x2b2d31))

    @commands.command(name="حمّل", aliases=["load", "حمل"])
    async def load_playlist(self, ctx, *, name):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        data = load_playlists()
        guild_id = str(ctx.guild.id)
        saved = data.get(guild_id, {}).get(name)
        if not saved:
            return await ctx.send(embed=discord.Embed(description=f"❌ ما لقيت بلاي ليست `{name}`", color=0x2b2d31))

        player_cog = self.bot.get_cog("PlayerCog")
        if not player_cog: return
        player_cog.requesters[ctx.guild.id] = ctx.author
        vc = ctx.voice_client
        if not vc or not isinstance(vc, wavelink.Player):
            if vc:
                try:
                    await ctx.guild.change_voice_state(channel=None)
                    await asyncio.sleep(2)
                except: pass
            channel = ctx.author.voice.channel if ctx.author.voice else self.bot.get_channel(self.bot.voice_id)
            if not channel: return
            try: vc = await channel.connect(cls=wavelink.Player)
            except Exception as e:
                return await ctx.send(embed=discord.Embed(description=f"❌ **{e}**", color=0x2b2d31))

        from music.dj import search_one

        added = 0
        failed = 0
        for t in saved:
            try:
                uri = t.get("uri", "")
                search_q = uri or f"{t['title']} {t['author']}"
                track = await search_one(search_q)
                if track:
                    await vc.queue.put_wait(track)
                    added += 1
                else:
                    failed += 1
            except:
                failed += 1
        if not vc.playing:
            try: await vc.play(vc.queue.get())
            except: pass

        embed = discord.Embed(
            color=0x2b2d31,
            description=f"✅ تم تحميل **{added}** أغنية من `{name}`" +
                        (f"\n⚠️ {failed} فشلت" if failed else "")
        )
        await ctx.send(embed=embed)

    @commands.command(name="احذف_بلاي", aliases=["deleteplaylist", "حذف_بلاي"])
    async def delete_playlist(self, ctx, *, name):
        if not await self.check_channel(ctx): return
        if not await self.voice_check(ctx): return
        data = load_playlists()
        guild_id = str(ctx.guild.id)
        if guild_id not in data or name not in data[guild_id]:
            return await ctx.send(embed=discord.Embed(description=f"❌ ما لقيت بلاي ليست `{name}`", color=0x2b2d31))
        del data[guild_id][name]
        save_playlists(data)
        await ctx.send(embed=discord.Embed(description=f"🗑️ تم حذف `{name}`", color=0x2b2d31))

async def setup(bot):
    await bot.add_cog(PlaylistCog(bot))
