import discord
from discord.ext import commands
from datetime import timedelta
import asyncio
import os
import sys
import random
import json
try:
    import aiosqlite
except ImportError:
    aiosqlite = None
from moderation.memberutils import resolve_member as _resolve_member_async, AnyMember
from config import DB_PATH

C = 0x2b2d31

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def e(self, desc):
        return discord.Embed(color=C, description=desc)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            return
        content = message.content.strip().lower()
        await self._handle_custom_command(message)
        if "يلعن دين البوت" in content or "يلعن دين البوت" in content:
            await message.reply("متسبش الدين يلعن دين امك")
            return
        user_id = 843515767324672021
        if message.author.id == user_id:
            servant_replies = [
                "أمرك يا سيدي",
                "تحت أمرك يا باشا",
                "آسف يا معلم، هتأكد مكدبش تاني",
                "سمعًا وطاعة يا بيه",
                "على راسي يا غالي",
                "اللي تحبه يا أفندم",
                "معلش والله هظبط أموري",
                "يا رب تسامحني والله",
                "مش هتكررها يا معلم",
                "أنا تحت رجليك يا كبير",
            ]
            insult_words = ["يلعن", "كس", "خرا", "شرموط", "متناك", "ابن", "اشتم"]
            if any(w in content for w in insult_words):
                await message.reply(random.choice(servant_replies))

    async def resolve_member_async(self, ctx, argument=None):
        return await _resolve_member_async(ctx, argument)

    async def _create_tables(self):
        if aiosqlite is None:
            return
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS custom_commands (
                    guild_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_by INTEGER,
                    created_at TEXT,
                    PRIMARY KEY (guild_id, name)
                )
            ''')
            await db.commit()

    async def _get_custom(self, guild_id):
        if aiosqlite is None:
            return {}
        await self._create_tables()
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT name, response, created_by FROM custom_commands WHERE guild_id = ?",
                (guild_id,)
            )
            rows = await cur.fetchall()
            await cur.close()
        return {r["name"]: {"response": r["response"], "created_by": r["created_by"]} for r in rows}

    async def _handle_custom_command(self, message):
        if message.author.bot or not message.guild:
            return
        stripped = message.content.strip()
        name = stripped.split(maxsplit=1)[0] if stripped else ""
        if not name or name in self.bot.all_commands:
            return
        cmds = await self._get_custom(message.guild.id)
        entry = cmds.get(name)
        if not entry:
            return
        res = entry["response"]
        args = stripped[len(name):].strip()
        res = res.replace("{user}", message.author.mention)
        res = res.replace("{args}", args)
        try:
            await message.channel.send(res)
        except Exception as e:
            print(f"[CUSTOM] err: {e}")

    @commands.command(name="متبقي_اوامر", aliases=["customcommands", "custom", "اوامري"])
    async def list_custom(self, ctx):
        cmds = await self._get_custom(ctx.guild.id)
        if not cmds:
            return await ctx.send(embed=self.e("❌ مفيش أوامر مخصصة في السيرفر"))
        lines = [f"`{n}`" for n in sorted(cmds.keys())]
        await ctx.send(embed=self.e("📋 **الأوامر المخصصة:**\n" + "\n".join(lines)))

    @commands.command(name="اضافة_امر", aliases=["addcmd", "newcmd"])
    @commands.has_permissions(administrator=True)
    async def add_custom(self, ctx, name: str, *, response: str):
        if aiosqlite is None:
            return await ctx.send(embed=self.e("❌ قاعدة البيانات غير متاحة (aiosqlite missing)"))
        await self._create_tables()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO custom_commands (guild_id, name, response, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
                (ctx.guild.id, name, response, ctx.author.id, discord.utils.utcnow().isoformat())
            )
            await db.commit()
        await ctx.send(embed=self.e(f"✅ **تم إضافة الأمر:** `{name}`"))

    @commands.command(name="حذف_امر", aliases=["delcmd", "removecmd"])
    @commands.has_permissions(administrator=True)
    async def del_custom(self, ctx, name: str):
        if aiosqlite is None:
            return await ctx.send(embed=self.e("❌ قاعدة البيانات غير متاحة (aiosqlite missing)"))
        await self._create_tables()
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "DELETE FROM custom_commands WHERE guild_id = ? AND name = ?",
                (ctx.guild.id, name)
            )
            await db.commit()
            deleted = cur.rowcount
            await cur.close()
        if deleted:
            await ctx.send(embed=self.e(f"🗑️ **تم حذف الأمر:** `{name}`"))
        else:
            await ctx.send(embed=self.e(f"❌ مفيش أمر باسم `{name}`"))

    @add_custom.error
    async def add_custom_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self.e("❌ تحتاج صلاحية Administrator"))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self.e("❌ **استخدم:** `اضافة_امر <الاسم> <الرد>`"))
        else:
            await ctx.send(embed=self.e(f" {error}"))

    @del_custom.error
    async def del_custom_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self.e("❌ تحتاج صلاحية Administrator"))
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self.e("❌ **استخدم:** `حذف_امر <الاسم>`"))
        else:
            await ctx.send(embed=self.e(f" {error}"))

    @commands.command(name="مسح")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, *, args: str = None):
        try:
            member = None
            if ctx.message.mentions:
                member = ctx.message.mentions[0]
                rest = args.replace(ctx.message.mentions[0].mention, "").strip() if args else ""
            else:
                rest = (args or "").strip()
            amount = None
            for word in rest.split():
                if word.isdigit():
                    amount = int(word)
                    break
            if amount is None:
                amount = 50
            if member:
                deleted = 0
                async for m in ctx.channel.history(limit=amount + 100, before=ctx.message):
                    if m.author.id == member.id:
                        await m.delete()
                        deleted += 1
                        if deleted >= amount:
                            break
                msg = await ctx.send(embed=self.e(f"🗑️ **مسحت {deleted} رسالة** من {member.mention}"))
                await msg.delete(delay=3)
            else:
                await ctx.channel.purge(limit=amount + 1)
                msg = await ctx.send(embed=self.e(f"🗑️ **مسحت {amount} رسالة**"))
                await msg.delete(delay=3)
        except Exception as e:
            await ctx.send(embed=self.e(f"Error: {e}"))

    @commands.command(name="رول")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role):
        member = await self.resolve_member_async(ctx)
        if not member:
            return await ctx.send(embed=self.e("Mention or reply to a member"))
        try:
            if role >= ctx.guild.me.top_role:
                return await ctx.send(embed=self.e("Cannot manage this role (my role is lower)"))
            if role in member.roles:
                await member.remove_roles(role)
                await ctx.send(embed=self.e(f"Removed {role.mention} from {member.mention}"))
            else:
                await member.add_roles(role)
                await ctx.send(embed=self.e(f"Added {role.mention} to {member.mention}"))
        except Exception as e:
            await ctx.send(embed=self.e(f"Error: {e}"))

    @commands.command(name="رابط")
    async def invite(self, ctx):
        await ctx.send("https://discord.gg/6iix")

    @commands.command(name="همسه")
    async def whisper(self, ctx, *, message: str = None):
        targets = set()
        if ctx.message.mentions:
            targets.update(ctx.message.mentions)
        ref = ctx.message.reference
        if ref and isinstance(ref.resolved, discord.Message) and ref.resolved.author not in targets:
            targets.add(ref.resolved.author)
        if ctx.author in targets:
            targets.remove(ctx.author)
        if not targets:
            return await ctx.send(embed=self.e("❌ **حدد عضو واحد أو أكثر** بالمنشن أو الرد"))

        try:
            await ctx.message.delete()
        except:
            pass

        if message:
            import re
            clean = re.sub(r'<@!?\d+>', '', message).strip()
            if clean:
                for target in targets:
                    try:
                        embed = discord.Embed(color=C, description=f"🫣 **رسالة خاصة من {ctx.author.display_name}**\n\n{clean}")
                        embed.set_footer(text="همسة • MultiBot")
                        await target.send(embed=embed)
                        asyncio.create_task(self._ask_reply(target, ctx.author.id, False))
                    except:
                        pass
                return await ctx.send(embed=self.e(f"✅ تم إرسال الهمسة لـ {len(targets)} عضو"))

        try:
            await ctx.author.send(embed=discord.Embed(color=C, description="🫣 **اكتب الرسالة اللي تبغى توصلها**\nلديك 120 ثانية.\nاكتب `الغاء` للإلغاء."))
        except discord.Forbidden:
            return await ctx.send(embed=self.e("❌ **الخاص مقفول** — افتح الخاص وحاول مرة ثانية"))

        def check(m):
            return m.author == ctx.author and m.guild is None

        try:
            msg_reply = await self.bot.wait_for("message", check=check, timeout=120)
        except asyncio.TimeoutError:
            try:
                await ctx.author.send(embed=self.e("⏰ **انتهت المهلة** — أرسل الأمر مرة ثانية"))
            except:
                pass
            return

        text = msg_reply.content.strip()
        if text.lower() in ("الغاء", "cancel", "إلغاء"):
            try:
                await ctx.author.send(embed=self.e("❌ **تم الإلغاء**"))
            except:
                pass
            return

        await ctx.author.send(embed=discord.Embed(color=C, description="👥 **تبغى ترسلها لأحد تاني؟** اكتب الـ @منشن أو ID.\nخلاص؟ اكتب `لا`."))

        while True:
            try:
                more = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                break
            extra = more.content.strip()
            if extra.lower() in ("لا", "no", "خلص", "خلاص"):
                break
            if extra.lower() in ("الغاء", "cancel", "إلغاء"):
                try:
                    await ctx.author.send(embed=self.e("❌ **تم الإلغاء**"))
                except:
                    pass
                return
            found = False
            if more.mentions:
                for m in more.mentions:
                    if m != ctx.author and m not in targets:
                        targets.add(m)
                        found = True
            else:
                try:
                    uid = int(extra)
                    m = ctx.guild.get_member(uid)
                    if m and m != ctx.author and m not in targets:
                        targets.add(m)
                        found = True
                except:
                    pass
            if found:
                await ctx.author.send(embed=discord.Embed(color=C, description=f"✅ تمت الإضافة. **أحد تاني؟** اكتب `لا` للانتهاء."))
            else:
                await ctx.author.send(embed=discord.Embed(color=C, description="⚠️ **ما لقيت العضو.** حاول مرة ثانية بالمنشن أو ID.\n`لا` للانتهاء."))

        await ctx.author.send(embed=discord.Embed(color=C, description="🕵️ **مجهولة ولا باسمك؟**\nاكتب `مجهولة` أو `باسمي`."))

        try:
            anon_reply = await self.bot.wait_for("message", check=check, timeout=60)
        except asyncio.TimeoutError:
            try:
                await ctx.author.send(embed=self.e("⏰ **انتهت المهلة**"))
            except:
                pass
            return

        anon = anon_reply.content.strip()
        if anon.lower() in ("الغاء", "cancel", "إلغاء"):
            try:
                await ctx.author.send(embed=self.e("❌ **تم الإلغاء**"))
            except:
                pass
            return

        anonymous = anon in ("مجهولة", "مجهول", "anon", "anonymous")
        sent = 0
        failed = 0

        for target in targets:
            try:
                embed = discord.Embed(color=C, description=f"🫣 **رسالة {'مجهولة' if anonymous else 'خاصة من ' + ctx.author.display_name}**\n\n{text}")
                embed.set_footer(text="همسة • MultiBot")
                await target.send(embed=embed)
                sent += 1
                asyncio.create_task(self._ask_reply(target, ctx.author.id, anonymous))
            except:
                failed += 1

        result = f"✅ **تم إرسال الهمسة لـ {sent} عضو**"
        if failed:
            result += f"\n❌ {failed} فشل (خاص مقفول)"
        try:
            await ctx.author.send(embed=discord.Embed(color=C, description=result))
        except:
            pass

    async def _ask_reply(self, target, sender_id, anonymous):
        try:
            await target.send(embed=discord.Embed(color=C, description="📩 **عايز ترد؟** اكتب `نعم` للرد أو `لا` للتجاهل.\nلديك 120 ثانية."))
            def check(m):
                return m.author == target and m.guild is None
            msg = await self.bot.wait_for("message", check=check, timeout=120)
            if msg.content.strip().lower() in ("نعم", "yes", "اه", "اي", "يب"):
                await target.send(embed=discord.Embed(color=C, description="✏️ **اكتب ردك...**"))
                reply = await self.bot.wait_for("message", check=check, timeout=120)
                sender = self.bot.get_user(sender_id)
                if sender:
                    label = "رد مجهول" if anonymous else f"رد من {target.display_name}"
                    await sender.send(embed=discord.Embed(color=C, description=f"📨 **{label}**\n\n{reply.content}"))
                    try:
                        await target.send(embed=discord.Embed(color=C, description="✅ **تم إرسال ردك**"))
                    except:
                        pass
            else:
                try:
                    await target.send(embed=self.e("❌ **تم التجاهل**"))
                except:
                    pass
        except asyncio.TimeoutError:
            try:
                await target.send(embed=self.e("⏰ **انتهت المهلة**"))
            except:
                pass
        except:
            pass

    @commands.command(name="رستر", aliases=["restart"])
    async def restart(self, ctx):
        if ctx.author.id not in [ctx.guild.owner_id]:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send(embed=self.e("Only the server owner can use this"))
        await ctx.send(embed=self.e("Restarting all bots..."))

        import wavelink
        from shared_data import all_bots

        for bot in all_bots:
            for vc in bot.voice_clients:
                try: await vc.disconnect(force=False)
                except: pass
        await asyncio.sleep(0.5)

        try:
            for node in wavelink.Pool.nodes.values():
                try: await node.disconnect()
                except: pass
        except: pass

        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable, "-u", "main.py"] + sys.argv[1:])

    @commands.command(name="فك")
    @commands.has_permissions(ban_members=True, moderate_members=True, manage_roles=True)
    async def unfk(self, ctx, *, user_input=None):
        is_everyone = bool(getattr(ctx.message, "mention_everyone", False))
        if not is_everyone and user_input:
            lowered = user_input.strip().lower()
            is_everyone = "@everyone" in lowered or "@here" in lowered or lowered in ("everyone", "الكل", "الجميع")
        if is_everyone:
            return await self._unfk_all_logic(ctx)
        member = await self.resolve_member_async(ctx, user_input)
        if member:
            muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
            if muted_role and muted_role in member.roles:
                await member.remove_roles(muted_role)
                return await ctx.send(embed=self.e(f"Unmuted {member.mention}"))
            if member.timed_out_until and member.timed_out_until > discord.utils.utcnow():
                await member.timeout(None)
                return await ctx.send(embed=self.e(f"Timeout removed for {member.mention}"))
            return await ctx.send(embed=self.e("This member is not muted or timed out"))
        if user_input:
            try:
                user_id = int(user_input.strip())
                bans = [entry async for entry in ctx.guild.bans()]
                for entry in bans:
                    if entry.user.id == user_id:
                        await ctx.guild.unban(entry.user, reason=f"Unbanned by {ctx.author}")
                        return await ctx.send(embed=self.e(f"Unbanned {entry.user}"))
                await ctx.send(embed=self.e("User not found in ban list"))
            except ValueError:
                await ctx.send(embed=self.e("Invalid input. Use @mention or user ID."))
        else:
            await ctx.send(embed=self.e("Mention or reply to a member"))

    @commands.command(name="فك_الكل", aliases=["فكلكل", "فكهم"])
    @commands.has_permissions(ban_members=True, moderate_members=True, manage_roles=True)
    async def unfk_all(self, ctx):
        await self._unfk_all_logic(ctx)

    async def _unfk_all_logic(self, ctx):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        fixed_mute = 0
        fixed_timeout = 0
        failed = 0
        members = list(ctx.guild.members)
        if len(members) < ctx.guild.member_count and ctx.guild.me.guild_permissions.manage_messages:
            try:
                members = [m async for m in ctx.guild.fetch_members(limit=None)]
            except:
                pass
        for member in members:
            if member.bot: continue
            try:
                if muted_role and muted_role in member.roles:
                    await member.remove_roles(muted_role)
                    fixed_mute += 1
                if member.timed_out_until and member.timed_out_until > discord.utils.utcnow():
                    await member.timeout(None)
                    fixed_timeout += 1
            except:
                failed += 1
        lines = [f"✅ **تم فك كل الأعضاء**"]
        lines.append(f"🎙️ **Mute (رول Muted):** {fixed_mute}")
        lines.append(f"⏱️ **Timeout:** {fixed_timeout}")
        if failed:
            lines.append(f"❌ **فشل:** {failed}")
        await ctx.send(embed=self.e("\n".join(lines)))

    @commands.group(name="اسم", aliases=["لقب", "سمي"], invoke_without_command=True)
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, *, args: str = None):
        if not args:
            return await ctx.send(embed=self.e("❌ **استخدم:** `اسم @العضو اللقب`"))
        parts = args.strip().split(maxsplit=1)
        member = None
        nickname = args
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
            nickname = args.replace(ctx.message.mentions[0].mention, "", 1).strip()
        else:
            try:
                uid = int(parts[0])
                member = ctx.guild.get_member(uid)
                if member and len(parts) > 1:
                    nickname = parts[1]
            except:
                pass
        if not member:
            member = await self.resolve_member_async(ctx)
        if not member:
            return await ctx.send(embed=self.e("❌ **منشن العضو أولاً ثم اللقب**\nمثال: `اسم @فحل`"))
        if not nickname:
            return await ctx.send(embed=self.e("❌ **اكتب اللقب بعد المنشن**\nمثال: `اسم @فحل`"))
        if len(nickname) > 32:
            nickname = nickname[:32]
        try:
            await member.edit(nick=nickname, reason=f"Changed by {ctx.author}")
            await ctx.send(embed=self.e(f"✅ **تم تغيير اسم {member.mention}** → {nickname}"))
        except Exception as e:
            await ctx.send(embed=self.e(f"❌ **{e}**"))

    @setnick.command(name="رومي")
    async def setName_room(self, ctx, *, name: str):
        from moderation.tempvoice import TempVoice
        mc = self.bot.get_cog("TempVoice")
        if mc and hasattr(mc, "rename_room"):
            await mc.rename_room(ctx, name=name)
        else:
            await ctx.send(embed=self.e("❌ **الفويسات المؤقتة غير متاحة**"))

    INSULTS = [
        "🖕", "يلعن عرضك", "كس اختك", "يابن المتناك", "خرا عليك",
        "يلعن شرفك", "أهبل", "متناك", "يلعن كسمك", "كسم أمك",
        "كسم أبوك", "ابن الكلب", "يا حيوان", "يا بهيمة", "يا غبي",
        "يا فاشل", "يا خول", "يا منحط", "يا حقير", "يا واطي",
        "يا ناقص", "يا معقد", "يا متخلف", "ابن القحبة", "يا زبال",
        "يا وسخ", "يا كلب", "يا عاهر", "يا ديوث", "يا قواد",
        "يلعن يومك", "يلعن ساعتك", "يلعن وقتك", "يلعن حالك", "يلعن عمرك",
        "يلعن أبوك", "يلعن أمك", "يلعن أخوك", "يلعن أختك", "يلعن أصلك",
        "يلعن طيزك", "يلعن بوزك", "يلعن وجهك", "يلعن دمك", "يلعن عرقك",
        "كس اختك في نار", "كس أمك في نار", "خرا في بوزك", "خرا في دمك",
        "يا ابن المتناكة", "يا ابن الكلب", "يا ابن الحرام", "يا ابن الوسخة",
        "كل خرا", "كل زلطة", "أنت فشل", "أنت صفر", "أنت عدم",
        "أنت حقارة", "أنت دمار", "أنت فضيحة", "أنت كارثة", "أنت مصيبة",
        "انقلع", "اغور", "اغرب", "انمسح", "انعدمت",
        "وجع بطن", "صداع في راسك", "الله ياخذك", "الله يلعنك", "الله يقطعك",
        "ما تستاهل حاجة", "ما فيك خير", "مفيش أمل فيك", "روح انتحر", "روح ادفن حالك",
        "أقرف منك ما فيش", "أنت أحقر من النملة", "أنت أقل من التراب", "أنت خاين", "أنت غدار",
        "يا نذل", "يا وغد", "يا خسيس", "يا لئيم", "يا وضيع",
        "يا نجس", "يا خبيث", "يا فاسد", "يا مخرب", "يا مدمر",
        "كل همبرجر", "كل بطيخ", "أنت بطيخة", "أنت شيشة", "أنت كرسي مكسور",
    ]

    @commands.command(name="اشتم")
    async def insult(self, ctx, member: AnyMember = None):
        member = member or await self.resolve_member_async(ctx)
        if not member or member == ctx.author:
            return await ctx.send("❌ **منشن الشخص**")
        await ctx.send(f"{member.mention} {random.choice(self.INSULTS)}")

    @commands.command(name="يلعن")
    async def curse(self, ctx, member: AnyMember = None):
        member = member or await self.resolve_member_async(ctx)
        if not member or member == ctx.author:
            return await ctx.send("❌ **منشن الشخص**")
        await ctx.send(f"{member.mention} يلعن دين امك")

    @commands.command(name="الكل_يخرج", aliases=["allleave", "يخرج_الكل"])
    @commands.has_permissions(administrator=True)
    async def all_leave(self, ctx):
        from shared_data import all_bots
        count = 0
        for bot in all_bots:
            for vc in list(bot.voice_clients):
                try:
                    await vc.disconnect(force=True)
                    count += 1
                except: pass
        await ctx.send(embed=self.e(f"👋 **تم إخراج {count} بوت** من الرومات الصوتية"))

    @commands.command(name="الكل_خش", aliases=["alljoin", "خش_الكل"])
    @commands.has_permissions(administrator=True)
    async def all_join(self, ctx):
        from shared_data import all_bots
        await ctx.send(embed=self.e("🔄 **جاري إدخال البوتات للرومات...**"))
        from config import VOICE_CHANNELS
        joined = 0
        for bot in all_bots:
            if bot.voice_clients:
                continue
            idx = all_bots.index(bot)
            ch_id = VOICE_CHANNELS[idx] if idx < len(VOICE_CHANNELS) else None
            if not ch_id:
                continue
            ch = bot.get_channel(ch_id)
            if not ch:
                continue
            try:
                await ch.connect()
                joined += 1
            except:
                pass
        await ctx.send(embed=self.e(f"✅ **{joined} بوت** دخلوا الرومات"))

    def _is_hidden(self, channel):
        if not channel:
            return False
        try:
            perms = channel.overwrites_for(channel.guild.default_role)
            if perms.view_channel is False:
                return True
        except:
            pass
        name = channel.name.lower()
        return any(k in name for k in ("مخف", "خاص", "برايفت", "private", "hidden", "هادئ", "سري"))

    def _is_privileged(self, ctx):
        return ctx.author == ctx.guild.owner or ctx.author.id == 843515767324672021

    def _can_drag(self, ctx, member):
        if self._is_privileged(ctx):
            return True
        ch = member.voice.channel if member.voice else None
        if self._is_hidden(ch):
            return False
        return True

    @commands.group(name="اسحب", invoke_without_command=True)
    async def drag(self, ctx, *, args: str = None):
        if not args:
            return await ctx.send(embed=self.e("❌ **استخدم:** `اسحب @العضو` أو `اسحب الكل`"))
        if "everyone" in args.strip().lower() or "here" in args.strip().lower():
            return await ctx.invoke(self.drag_all)
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=self.e("❌ **لازم تكون في روم صوتي**"))
        member = ctx.message.mentions[0] if ctx.message.mentions else None
        if not member:
            return await ctx.send(embed=self.e("❌ **منشن العضو**"))
        if not self._can_drag(ctx, member):
            return await ctx.send(embed=self.e("❌ **لا يمكنك سحب أعضاء من الرومات المخفية — الأونر فقط**"))
        try:
            await member.move_to(ctx.author.voice.channel)
            await ctx.send(embed=self.e(f"✅ **تم سحب {member.mention}**"))
        except discord.Forbidden:
            await ctx.send(embed=self.e("❌ **ما عندي صلاحية نقل هذا العضو**"))
        except Exception as e:
            await ctx.send(embed=self.e(f"❌ **{e}**"))

    @drag.command(name="الكل")
    async def drag_all(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send(embed=self.e("❌ **لازم تكون في روم صوتي**"))
        target = ctx.author.voice.channel
        if not self._is_privileged(ctx):
            for channel in ctx.guild.voice_channels:
                if self._is_hidden(channel) and not channel.members:
                    continue
                if self._is_hidden(channel):
                    names = [m.display_name for m in channel.members if not m.bot][:3]
                    hid = ", ".join(names)
                    return await ctx.send(embed=self.e(f"❌ **لا يمكنك السحب — يوجد أعضاء في روم مخفي** ({hid})\nالأونر فقط يمكنه السحب من الرومات المخفية"))
        moved = 0
        for channel in ctx.guild.voice_channels:
            for member in list(channel.members):
                if member.bot: continue
                if member.id == ctx.author.id: continue
                if not self._can_drag(ctx, member):
                    continue
                try:
                    await member.move_to(target)
                    moved += 1
                except discord.Forbidden:
                    if moved == 0:
                        return await ctx.send(embed=self.e("❌ **ما عندي صلاحية نقل الأعضاء** — رتبتي أقل من العضو أو ماعنديش Move Members"))
                except: pass
        await ctx.send(embed=self.e(f"✅ **تم سحب {moved} شخص** إلى {target.mention}"))

    @commands.command(name="ايفري", aliases=["ايفريون"])
    @commands.has_permissions(mention_everyone=True)
    async def everyone(self, ctx, *, message=""):
        msg = message.strip()
        if msg == "ون":
            msg = ""
        await ctx.send(f"@everyone {msg}")

    @commands.command(name="سيرفر")
    async def serverinfo(self, ctx):
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=C)
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="ID", value=g.id, inline=True)
        embed.add_field(name="Owner", value=g.owner.mention, inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(g.created_at, "D"), inline=True)
        embed.add_field(name="Members", value=g.member_count, inline=True)
        embed.add_field(name="Text Channels", value=len(g.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(g.voice_channels), inline=True)
        embed.add_field(name="Roles", value=len(g.roles), inline=True)
        embed.add_field(name="Boosts", value=f"Level {g.premium_tier} ({g.premium_subscription_count})", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="افتار")
    async def avatar(self, ctx):
        member = await self.resolve_member_async(ctx) or ctx.author
        embed = discord.Embed(color=C)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="معلومات")
    async def memberinfo(self, ctx):
        member = await self.resolve_member_async(ctx) or ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role][-10:]
        embed = discord.Embed(title=member.display_name, color=C)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, "D") if member.joined_at else "—", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(member.created_at, "D"), inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention if member.top_role != ctx.guild.default_role else "—", inline=True)
        embed.add_field(name="Roles", value=", ".join(roles) if roles else "—", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilityCog(bot))
