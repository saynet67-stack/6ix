import discord
from discord.ext import commands
import json
import os
import asyncio
import datetime

C = 0x2b2d31
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "temp_rooms.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class TempVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._delete_tasks = {}

    # ── Create room: افتح [فويس] [الاسم] ──

    @commands.group(name="افتح", aliases=["اعمل"], invoke_without_command=True)
    async def open_music(self, ctx, *, name: str = None):
        if self.bot.number != 1:
            return
        await self._create_room_logic(ctx, name)

    @open_music.command(name="فويس")
    async def open_voice(self, ctx, *, name: str = None):
        if self.bot.number != 1:
            return
        await self._create_room_logic(ctx, name)

    async def _create_room_logic(self, ctx, name: str = None):
        if not name:
            await ctx.send(embed=discord.Embed(color=C, description="✏️ **اكتب اسم الفويس اللي عايزه**\nلديك 60 ثانية.\n`الغاء` للإلغاء."))

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                name_msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send(embed=discord.Embed(color=C, description="⏰ **انتهت المهلة**"))

            name = name_msg.content.strip()
            if name.lower() in ("الغاء", "cancel", "إلغاء"):
                return await ctx.send(embed=discord.Embed(color=C, description="❌ **تم الإلغاء**"))

        name = name.strip()
        if name.lower() in ("الغاء", "cancel", "إلغاء"):
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **تم الإلغاء**"))
        if len(name) > 50:
            name = name[:50]

        temp = await self._create_channel(ctx, name)
        if not temp:
            return

        config = load_config()
        gid = str(ctx.guild.id)
        if gid not in config:
            config[gid] = {}
        config[gid].setdefault("active_rooms", {})[str(temp.id)] = {
            "owner": ctx.author.id,
            "created_at": datetime.datetime.now().isoformat()
        }
        save_config(config)

        self._schedule_delete(temp)

        await ctx.send(embed=discord.Embed(color=C, description=f"✅ **تم إنشاء فويسك** `{name}`\nأوامر التحكم:\n`اسم رومي` • `حد رومي` • `قفل رومي` • `فتح رومي` • `اقفل الفويس`"))

    async def _create_channel(self, ctx, name):
        if ctx.author.voice and ctx.author.voice.channel:
            category = ctx.author.voice.channel.category
        else:
            category = None
            for ch in ctx.guild.channels:
                if isinstance(ch, discord.CategoryChannel):
                    category = ch
                    break

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
            ctx.author: discord.PermissionOverwrite(
                manage_channels=True, connect=True, speak=True,
                mute_members=True, deafen_members=True, move_members=True
            )
        }

        try:
            temp = await ctx.guild.create_voice_channel(name=name, category=category, overwrites=overwrites)
            if ctx.author.voice and ctx.author.voice.channel:
                try:
                    await ctx.author.move_to(temp)
                except:
                    pass
            return temp
        except Exception as e:
            await ctx.send(embed=discord.Embed(color=C, description=f"❌ **{e}**"))
            return None

    # ── اسم رومي ──
    async def rename_room(self, ctx, *, name: str = None):
        if self.bot.number != 1:
            return
        if not name:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **استخدم:** `اسم رومي <الاسم الجديد>`"))

        # يقبل "رومي الاسم" أو الاسم مباشرة
        if name.lower().startswith("رومي "):
            name = name[5:].strip()

        if not name:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **استخدم:** `اسم رومي <الاسم الجديد>`"))

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **لازم تكون في روم صوتي**"))

        ch = ctx.author.voice.channel
        config = load_config()
        gid = str(ctx.guild.id)
        info = config.get(gid, {}).get("active_rooms", {}).get(str(ch.id))

        if not info or info["owner"] != ctx.author.id:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويسك**"))

        if len(name) > 50:
            name = name[:50]

        await ch.edit(name=name)
        await ctx.send(embed=discord.Embed(color=C, description=f"✅ **تم تغيير الاسم** → `{name}`"))

    # ── حد رومي ──
    @commands.group(name="حد", invoke_without_command=True)
    async def limit_group(self, ctx, *, rest: str = None):
        await ctx.send(embed=discord.Embed(color=C, description="❌ **استخدم:** `حد رومي <الرقم>`"))

    @limit_group.command(name="رومي")
    async def room_limit(self, ctx, limit: int):
        if self.bot.number != 1:
            return
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **لازم تكون في روم صوتي**"))

        ch = ctx.author.voice.channel
        config = load_config()
        gid = str(ctx.guild.id)
        info = config.get(gid, {}).get("active_rooms", {}).get(str(ch.id))

        if not info or info["owner"] != ctx.author.id:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويسك**"))

        if limit < 0 or limit > 99:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **الحد من 0 إلى 99**\n0 = مفتوح"))

        await ch.edit(user_limit=limit)
        await ctx.send(embed=discord.Embed(color=C, description=f"✅ **تم تعيين الحد** → {'مفتوح' if limit == 0 else str(limit)}"))

    # ── قفل رومي / فتح رومي ──
    async def lock_room(self, ctx):
        if self.bot.number != 1:
            return
        await ctx.defer() if hasattr(ctx, 'interaction') and ctx.interaction else None
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **لازم تكون في روم صوتي**"))

        ch = ctx.author.voice.channel
        config = load_config()
        gid = str(ctx.guild.id)
        info = config.get(gid, {}).get("active_rooms", {}).get(str(ch.id))

        if not info or info["owner"] != ctx.author.id:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويسك**"))

        overwrites = ch.overwrites_for(ctx.guild.default_role)
        overwrites.connect = False
        await ch.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        await ctx.send(embed=discord.Embed(color=C, description="🔒 **تم قفل الروم**"))

    async def unlock_room(self, ctx):
        if self.bot.number != 1:
            return
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **لازم تكون في روم صوتي**"))

        ch = ctx.author.voice.channel
        config = load_config()
        gid = str(ctx.guild.id)
        info = config.get(gid, {}).get("active_rooms", {}).get(str(ch.id))

        if not info or info["owner"] != ctx.author.id:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويسك**"))

        overwrites = ch.overwrites_for(ctx.guild.default_role)
        overwrites.connect = True
        await ch.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        await ctx.send(embed=discord.Embed(color=C, description="🔓 **تم فتح الروم**"))

    # ── اقفل ──
    @commands.group(name="اقفل", invoke_without_command=True)
    async def close_music(self, ctx):
        if self.bot.number != 1:
            return
        # لوحده → يوقف الموسيقى
        mc = self.bot.get_cog("MusicCommandsCog")
        if mc and hasattr(mc, "stop"):
            await mc.stop(ctx)
        else:
            await ctx.send(embed=discord.Embed(color=C, description="❌ **أمر غير معروف — استخدم `اقفل الفويس` أو `اقفل الفويسات`**"))

    @close_music.command(name="الفويس")
    async def close_voice(self, ctx):
        if self.bot.number != 1:
            return
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **لازم تكون في روم صوتي**"))

        ch = ctx.author.voice.channel
        config = load_config()
        gid = str(ctx.guild.id)
        info = config.get(gid, {}).get("active_rooms", {}).get(str(ch.id))

        if not info:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويس مؤقت**"))
        if info["owner"] != ctx.author.id and ctx.author != ctx.guild.owner:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **ده مش فويسك**"))

        await self._delete_temp_room(ctx.guild, ch)
        await ctx.send(embed=discord.Embed(color=C, description="🗑️ **تم مسح الفويس**"))

    @close_music.command(name="الفويسات")
    async def close_all_rooms(self, ctx):
        if self.bot.number != 1:
            return
        config = load_config()
        gid = str(ctx.guild.id)
        active = config.get(gid, {}).get("active_rooms", {})
        if not active:
            return await ctx.send(embed=discord.Embed(color=C, description="❌ **مافيش فويسات مؤقتة**"))

        count = 0
        for cid in list(active.keys()):
            ch = ctx.guild.get_channel(int(cid))
            if ch:
                try:
                    await ch.delete()
                    count += 1
                except:
                    pass

        config[gid]["active_rooms"] = {}
        save_config(config)
        await ctx.send(embed=discord.Embed(color=C, description=f"✅ **تم مسح {count} فويس**"))

    async def _delete_temp_room(self, guild, channel):
        gid = str(guild.id)
        cid = str(channel.id)
        task = self._delete_tasks.pop(cid, None)
        if task and not task.done():
            task.cancel()
        try:
            await channel.delete()
        except:
            pass
        config = load_config()
        active = config.get(gid, {}).get("active_rooms", {})
        active.pop(cid, None)
        config.setdefault(gid, {})["active_rooms"] = active
        save_config(config)

    # ── Auto-delete after 10 min empty ──
    def _schedule_delete(self, channel):
        cid = str(channel.id)
        task = self._delete_tasks.get(cid)
        if task and not task.done():
            task.cancel()
        self._delete_tasks[cid] = asyncio.ensure_future(self._auto_delete_task(channel))

    def _cancel_delete(self, channel):
        cid = str(channel.id)
        task = self._delete_tasks.pop(cid, None)
        if task and not task.done():
            task.cancel()

    async def _auto_delete_task(self, channel):
        await asyncio.sleep(600)  # 10 minutes
        try:
            guild = channel.guild
            ch = guild.get_channel(channel.id)
            if ch and len(ch.members) == 0:
                await self._delete_temp_room(guild, ch)
        except Exception as e:
            print(f"[TEMPVC] auto-delete err: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or self.bot.number != 1:
            return
        config = load_config()
        gid = str(member.guild.id)
        active = config.get(gid, {}).get("active_rooms", {})

        if after.channel and str(after.channel.id) in active:
            self._cancel_delete(after.channel)

        if before.channel and str(before.channel.id) in active:
            ch = member.guild.get_channel(before.channel.id)
            if ch and len(ch.members) == 0:
                self._schedule_delete(before.channel)

async def setup(bot):
    await bot.add_cog(TempVoice(bot))