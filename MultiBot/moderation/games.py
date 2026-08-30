import discord
from discord.ext import commands
import asyncio
import random

# ألوان متنوعة للـ embeds
COLORS = {
    "primary": 0x2b2d31,
    "success": 0x57f287,
    "warning": 0xfee75c,
    "error": 0xed4245,
    "info": 0x5865f2,
    "music": 0x3ba55c,
    "game": 0x9b59b6,
    "mod": 0xe74c3c,
    "welcome": 0x3498db,
    "gold": 0xf1c40f,
    "purple": 0x9b59b6,
    "pink": 0xe91e63,
    "cyan": 0x00bcd4,
    "orange": 0xff9800,
}

C = COLORS["primary"]

WORDS = {
    "كرة": [
        "محمد صلاح", "ليونيل ميسي", "كريستيانو رونالدو", "نيمار", "كليان مبابي",
        "ريال مدريد", "برشلونة", "ليفربول", "مانشستر سيتي", "الأهلي المصري",
        "الهلال السعودي", "كأس العالم", "كأس أمم أفريقيا", "دوري أبطال أوروبا",
        "حارس مرمى", "ضربة جزاء", "ركلات ترجيح", "تسلل", "كارت أحمر", "ركنية",
        "تمريرة حاسمة", "هاتريك", "ثنائية", "انتصار", "تعادل", "خسارة",
        "فيرمينو", "دي بروين", "هالاند", "فينيسيوس", "فالفيردي", "بيلينغهام",
        "صلاح", "تريزيجيه", "محرز", "زياش", "أوزيل", "راموس", "بنزيما",
        "كورتوا", "نوير", "دي خيا", "حراس المرمى", "مدرب", "بطولة",
        "كرة قدم", "مرمى", "ملعب", "جمهور", "تشكيلة", "تبديل", "إصابة وقت بدل ضائع",
    ],
    "مشاهير": [
        "أحمد حلمي", "محمد هنيدي", "عادل إمام", "يوسف وهبي", "فيروز",
        "عمرو دياب", "محمد منير", "أنغام", "شيرين", "تامر حسني",
        "إليسا", "نانسي عجرم", "هيفاء وهبي", "مايا دياب", "كاظم الساهر",
        "إياد نصار", "كريم عبد العزيز", "يوسف الشريف", "أحمد الفيشاوي",
        "منى زكي", "ياسمين عبد العزيز", "مي عز الدين", "غادة عادل",
        "محمد رمضان", "أمير كرارة", "مصطفى شعبان", "حسن الرداد",
        "إيمي سمير غانم", "دينا الشربيني", "ليلى علوي", "يسرا",
        "إلون ماسك", "بيل غيتس", "مارك زوكربيرغ", "جيف بيزوس",
        "ميسي", "رونالدو", "صلاح", "ويز خليفة", "إيمينيم",
        "دريك", "بيونسيه", "تايلور سويفت", "أديل", "شاكيرا",
        "كيم كارداشيان", "كايلي جينر", "ليبرون جيمس", "أشر", "كريس براون",
    ],
    "خضروات": [
        "طماطم", "خيار", "جزر", "بطاطس", "بصل", "ثوم", "فلفل", "باذنجان",
        "كوسة", "قرع", "فاصوليا", "بازلاء", "عدس", "حمص", "فول",
        "سبانخ", "خس", "جرجير", "بقدونس", "كزبرة", "نعناع", "ريحان",
        "كرنب", "بروكلي", "قرنبيط", "كرفس", "بنجر", "بطاطا", "قلقاس",
        "زيتون", "خرشوف", "ملوخية", "بامية", "كراث", "زنجبيل",
        "فجل", "لفت", "جزر أبيض", "ساق", "سلق", "جرجير", "صويا",
        "خس", "بقدونس", "كزبرة خضراء", "حبق", "شبت", "كزبرة يابسة",
        "بصل أخضر", "ثوم معمر", "كراث", "هليون", "خيزران", "ذرة صفراء",
    ],
    "فاكهة": [
        "تفاح", "موز", "برتقال", "عنب", "فراولة", "مانجو", "أناناس",
        "بطيخ", "شمام", "كنتالوب", "خوخ", "مشمش", "كرز", "رمان",
        "توت", "توت بري", "كيوي", "أفوكادو", "ليمون", "جريب فروت",
        "يوسفي", "كمثرى", "لوز", "بندق", "عين جمل", "فستق", "كاجو",
        "تين", "بلح", "جوز الهند", "باباي", "جوافة", "مانغوستين",
        "دوريان", "فاكهة التنين", "ليتشي", "تمر هندي", "برقوق",
        "كاكا", "كريب فروت", "نكتارين", "توت شوكي", "توت أسود",
        "عنب أحمر", "تفاح أخضر", "ليمون أصفر", "يوسفي", "بوملي",
    ],
    "بلاد": [
        "مصر", "السعودية", "الإمارات", "الكويت", "قطر", "عمان", "البحرين",
        "العراق", "سوريا", "لبنان", "الأردن", "فلسطين", "اليمن",
        "المغرب", "الجزائر", "تونس", "ليبيا", "السودان",
        "تركيا", "إيران", "باكستان", "الهند", "الصين", "اليابان",
        "أمريكا", "كندا", "بريطانيا", "فرنسا", "ألمانيا", "إيطاليا",
        "إسبانيا", "البرتغال", "بلجيكا", "هولندا", "روسيا",
        "أستراليا", "نيوزيلندا", "البرازيل", "الأرجنتين",
        "جنوب أفريقيا", "نيجيريا", "كينيا", "إثيوبيا",
        "دبي", "باريس", "لندن", "نيويورك", "طوكيو", "روما",
    ],
    "ممثل مصري": [
        "عادل إمام", "أحمد حلمي", "محمد هنيدي", "كريم عبد العزيز", "أحمد السقا",
        "محمد رمضان", "أمير كرارة", "يوسف الشريف", "أحمد الفيشاوي", "هاني سلامة",
        "مصطفى شعبان", "حسن الرداد", "محمد إمام", "أحمد رزق", "عمرو واكد",
        "خالد أبو النجا", "خالد الصاوي", "ماجد الكدواني", "محمد فراج", "آسر ياسين",
        "بيومي فؤاد", "سعيد صالح", "فؤاد المهندس", "عبد المنعم مدبولي", "شكري سرحان",
        "رشدي أباظة", "فريد شوقي", "إسماعيل ياسين", "أنور وجدي", "يحيى الفخراني",
        "نور الشريف", "محمود عبد العزيز", "صلاح ذو الفقار", "عماد حمدي", "كمال الشناوي",
        "محمد صبحي", "سامح حسين", "هاني شاكر", "أحمد حلمي", "أشرف عبد الباقي",
        "علاء ولي الدين", "محمد سعد", "كريم محمود عبد العزيز", "محمد لطفي", "شيكو",
        "هشام ماجد", "أحمد فهمي", "علي ربيع", "أوس أوس", "مصطفى خاطر",
    ],
    "مغني مصري": [
        "عمرو دياب", "محمد منير", "تامر حسني", "محمد رمضان", "هاني شاكر",
        "كاظم الساهر", "أصالة", "أنغام", "شيرين", "إليسا",
        "حكيم", "حميد الشاعري", "محمد فؤاد", "مصطفى كامل", "إيهاب توفيق",
        "نوال الزغبي", "مي فاروق", "سارة الزكريا", "أمل حجازي", "كارمن سليمان",
        "حمزة نمرة", "عمر كمال", "حمو بيكا", "مسلم", "عفروتو",
        "أحمد سعد", "بهاء سلطان", "راغب علامة", "جورج وسوف", "وائل كفوري",
        "ماجد المهندس", "راشد الماجد", "أصيل هميم", "دالي", "محمد عبده",
        "أبو بكر سالم", "طلال مداح", "عبد المجيد عبد الله", "فهد الكبيسي", "حسين الجسمي",
        "بلقيس", "أحلام", "ماجدة الرومي", "فيروز", "صباح",
        "وديع الصافي", "نصري شمس الدين", "سميرة توفيق", "ميادة الحناوي", "عبد الحليم حافظ",
    ],
}

class HeadsUpGame:
    def __init__(self, ctx, team_a, team_b, category, words):
        self.ctx = ctx
        self.team_a = team_a
        self.team_b = team_b
        self.category = category
        self.words = words.copy()
        random.shuffle(self.words)
        self.word_index = 0
        self.score_a = 0
        self.score_b = 0
        self.round = 0
        self.active = True
        self.skip_votes = set()
        self.round_time = 60
        self.skip_msg = None

    def switch_teams(self):
        self.round += 1
        self.word_index = 0
        self.skip_votes.clear()

    @property
    def describers(self):
        return self.team_b if self.round % 2 == 0 else self.team_a

    @property
    def guessers(self):
        return self.team_a if self.round % 2 == 0 else self.team_b

    @property
    def scoring_team(self):
        return self.team_a if self.round % 2 == 0 else self.team_b

class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command(name="لعبه", aliases=["هيدز_آب", "heads_up", "علي_الجبهه", "الجبهه", "لعبة"])
    async def heads_up(self, ctx):
        if ctx.channel.id in self.active_games:
            return await ctx.send(embed=discord.Embed(color=COLORS["error"], description="❌ **في لعبة شغالة في الشات دا**"))

        view = TeamSelect(self)
        embed = discord.Embed(
            color=COLORS["game"],
            title="🎮 لعبة التخمين!",
            description="**اختار نظام اللعب:**\n\n"
                        "1️⃣ `1 ضد 1`\n"
                        "2️⃣ `2 ضد 2`\n"
                        "3️⃣ `3 ضد 3`\n"
                        "4️⃣ `4 ضد 4`\n"
                        "5️⃣ `5 ضد 5`"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890/1234567890/game.png")
        embed.set_footer(text="اضغط على الزر عشان تبدا")
        msg = await ctx.send(embed=embed, view=view)
        view.msg = msg
        await view.wait()

        if not view.mode:
            return

        team_size = view.mode
        await self._setup_teams(ctx, team_size)

    async def _setup_teams(self, ctx, team_size):
        view = TeamJoin(self, ctx.author, team_size)
        embed = discord.Embed(
            color=COLORS["info"],
            title=f"🎮 لعبة — {team_size} ضد {team_size}",
            description=f"**فريق A** ← يضغطون على الزر الأخضر\n"
                        f"**فريق B** ← يضغطون على الزر الأزرق\n\n"
                        f"مطلوب **{team_size}** لاعب لكل فريق\n"
                        f"اللاعبون الحاليون:"
        )
        embed.add_field(name="🟢 فريق A", value="—", inline=True)
        embed.add_field(name="🔵 فريق B", value="—", inline=True)
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890/1234567890/teams.png")
        embed.set_footer(text="اللعب يبدأ بعد اكتمال الفريقين")
        msg = await ctx.send(embed=embed, view=view)
        view.msg = msg
        await view.wait()

        if not view.team_a or not view.team_b:
            return await ctx.send(embed=discord.Embed(color=COLORS["error"], description="❌ **ما اكتملش العدد**"))

        await self._choose_category(ctx, view.team_a, view.team_b)

    async def _choose_category(self, ctx, team_a, team_b):
        view = CategorySelect()
        embed = discord.Embed(
            color=COLORS["purple"],
            title="🎯 اختار القسم",
            description="> ⚽ **كرة**\n> 🌟 **مشاهير**\n> 🥦 **خضروات**\n> 🍎 **فاكهة**\n> 🌍 **بلاد**\n> 🎭 **ممثل مصري**\n> 🎤 **مغني مصري**"
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890/1234567890/category.png")
        msg = await ctx.send(embed=embed, view=view)
        view.msg = msg
        await view.wait()

        if not view.category:
            return await ctx.send(embed=discord.Embed(color=COLORS["warning"], description="❌ **تم الإلغاء**"))

        await self._start_game(ctx, team_a, team_b, view.category)

    async def _start_game(self, ctx, team_a, team_b, category):
        words = WORDS.get(category, []).copy()
        if len(words) < 5:
            words = list(WORDS["كرة"])

        game = HeadsUpGame(ctx, team_a, team_b, category, words)
        self.active_games[ctx.channel.id] = game

        await ctx.send(embed=discord.Embed(
            color=C,
            description=f"🎮 **بدأت اللعبة!**\n"
                        f"القسم: **{category}**\n"
                        f"🟢 فريق A: {', '.join(m.mention for m in team_a)}\n"
                        f"🔵 فريق B: {', '.join(m.mention for m in team_b)}"
        ))
        await asyncio.sleep(2)
        await self._run_round(ctx, game)

    async def _run_round(self, ctx, game):
        if not game.active:
            return

        desc = game.describers
        guess = game.guessers
        scoring = game.scoring_team
        team_label = "A" if scoring == game.team_a else "B"

        skip_view = SkipVote(game)
        msg = await ctx.send(embed=discord.Embed(
            color=C,
            description=f"🔵 **دور فريق {team_label} يخمن!**\n"
                        f"الوصف: {', '.join(m.mention for m in desc)}\n"
                        f"التخمين: {', '.join(m.mention for m in guess)}\n"
                        f"⏱ {game.round_time} ثانية\n"
                        f"اضغط ⏭ للـ Skip"
        ), view=skip_view)
        skip_view.msg = msg

        round_embed = discord.Embed(color=C, title=f"🎯 الجولة {game.round + 1}")
        await ctx.send(embed=round_embed)

        for m in desc:
            try:
                await m.send(embed=discord.Embed(
                    color=C,
                    title="🧠 كلمتك",
                    description=f"**{game.words[game.word_index]}**"
                ))
            except:
                pass

        start = asyncio.get_event_loop().time()
        solved_this_round = 0

        while game.active and game.word_index < len(game.words):
            elapsed = asyncio.get_event_loop().time() - start
            remaining = game.round_time - elapsed
            if remaining <= 0:
                break

            word = game.words[game.word_index]

            def check(m):
                if m.channel.id != ctx.channel.id:
                    return False
                if m.author not in guess:
                    return False
                if m.content.startswith("⏭") or m.content == "⏭":
                    return False
                return True

            try:
                guess_msg = await self.bot.wait_for("message", check=check, timeout=remaining)
            except asyncio.TimeoutError:
                break

            content = guess_msg.content.strip().lower()
            word_lower = word.lower()

            if any(kw in content for kw in word_lower.split()) or content == word_lower:
                solved_this_round += 1
                if scoring == game.team_a:
                    game.score_a += 1
                else:
                    game.score_b += 1
                await ctx.send(f"✅ **{word}** — إجابة صحيحة! 🎉")
                game.word_index += 1
                await asyncio.sleep(1)

                if game.word_index < len(game.words):
                    for m in desc:
                        try:
                            await m.send(embed=discord.Embed(
                                color=C,
                                title="🧠 الكلمة الجديدة",
                                description=f"**{game.words[game.word_index]}**"
                            ))
                        except:
                            pass

        if not game.active:
            return

        if skip_view.msg:
            try:
                await skip_view.msg.edit(view=None)
            except:
                pass

        await ctx.send(embed=discord.Embed(
            color=C,
            description=f"⏰ **انتهى الوقت!**\n"
                        f"فريق {team_label} سجل **{solved_this_round}** نقاط\n\n"
                        f"📊 النتيجة: 🟢 {game.score_a} - {game.score_b} 🔵"
        ))
        await asyncio.sleep(3)

        if game.round >= 1:
            await self._end_game(ctx, game)
            return

        game.switch_teams()
        await self._run_round(ctx, game)

    async def _end_game(self, ctx, game):
        game.active = False
        self.active_games.pop(ctx.channel.id, None)

        if game.score_a > game.score_b:
            winner = "🟢 **فريق A** فاز! 🏆"
        elif game.score_b > game.score_a:
            winner = "🔵 **فريق B** فاز! 🏆"
        else:
            winner = "🤝 **تعادل!**"

        embed = discord.Embed(
            color=C,
            title="🎮 Heads Up! — انتهت اللعبة",
            description=f"{winner}\n\n"
                        f"🟢 فريق A: **{game.score_a}**\n"
                        f"🔵 فريق B: **{game.score_b}**"
        )
        await ctx.send(embed=embed)

class SkipVote(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        self.msg = None

    @discord.ui.button(emoji="⏭", style=discord.ButtonStyle.gray)
    async def skip_btn(self, i, b):
        self.game.skip_votes.add(i.user.id)
        needed = max(1, len(self.game.guessers) // 2 + 1)
        if len(self.game.skip_votes) >= needed:
            self.game.active = False
            try: await self.msg.edit(view=None)
            except: pass
            await self.game.ctx.send("⏭️ **تم التخطي** — صوت كافي!")
        else:
            try:
                await i.response.send_message(f"⏭️ **{len(self.game.skip_votes)}/{needed}** أصوات مطلوبة للـ Skip", ephemeral=True)
            except:
                pass

class TeamSelect(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        self.mode = None
        self.msg = None

    async def on_timeout(self):
        if self.msg:
            try: await self.msg.edit(view=None)
            except: pass

    @discord.ui.button(label="1 ضد 1", emoji="🎮", style=discord.ButtonStyle.primary)
    async def b1(self, i, b):
        try:
            self.mode = 1; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="2 ضد 2", emoji="🎮", style=discord.ButtonStyle.primary)
    async def b2(self, i, b):
        try:
            self.mode = 2; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="3 ضد 3", emoji="🎮", style=discord.ButtonStyle.primary)
    async def b3(self, i, b):
        try:
            self.mode = 3; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="4 ضد 4", emoji="🎮", style=discord.ButtonStyle.primary)
    async def b4(self, i, b):
        try:
            self.mode = 4; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="5 ضد 5", emoji="🎮", style=discord.ButtonStyle.primary)
    async def b5(self, i, b):
        try:
            self.mode = 5; self.stop()
            await i.response.defer()
        except: pass

class TeamJoin(discord.ui.View):
    def __init__(self, cog, starter, size):
        super().__init__(timeout=120)
        self.cog = cog
        self.starter = starter
        self.size = size
        self.team_a = [starter]
        self.team_b = []
        self.msg = None
        self.done = False

    async def on_timeout(self):
        if self.msg:
            try: await self.msg.edit(view=None)
            except: pass

    def build_embed(self):
        a = "\n".join(m.mention for m in self.team_a) if self.team_a else "—"
        b = "\n".join(m.mention for m in self.team_b) if self.team_b else "—"
        embed = discord.Embed(
            color=C,
            title=f"🎮 لعبة — {self.size} ضد {self.size}",
            description=f"{len(self.team_a)}/{self.size} 🟢 | {len(self.team_b)}/{self.size} 🔵"
        )
        embed.add_field(name="🟢 فريق A", value=a, inline=True)
        embed.add_field(name="🔵 فريق B", value=b, inline=True)
        return embed

    async def update(self):
        if self.msg:
            try:
                await self.msg.edit(embed=self.build_embed(), view=self)
            except:
                pass
        if len(self.team_a) >= self.size and len(self.team_b) >= self.size and not self.done:
            self.done = True
            self.stop()

    @discord.ui.button(label="🟢 فريق A", style=discord.ButtonStyle.green)
    async def join_a(self, i, b):
        try:
            if i.user in self.team_b:
                self.team_b.remove(i.user)
            if i.user not in self.team_a and len(self.team_a) < self.size:
                self.team_a.append(i.user)
            await self.update()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🔵 فريق B", style=discord.ButtonStyle.blurple)
    async def join_b(self, i, b):
        try:
            if i.user in self.team_a:
                self.team_a.remove(i.user)
            if i.user not in self.team_b and len(self.team_b) < self.size:
                self.team_b.append(i.user)
            await self.update()
            await i.response.defer()
        except: pass

class CategorySelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.category = None
        self.msg = None

    async def on_timeout(self):
        if self.msg:
            try: await self.msg.edit(view=None)
            except: pass

    @discord.ui.button(label="⚽ كرة", emoji="⚽", style=discord.ButtonStyle.secondary)
    async def cat1(self, i, b):
        try:
            self.category = "كرة"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🌟 مشاهير", emoji="🌟", style=discord.ButtonStyle.secondary)
    async def cat2(self, i, b):
        try:
            self.category = "مشاهير"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🥦 خضروات", emoji="🥦", style=discord.ButtonStyle.secondary)
    async def cat3(self, i, b):
        try:
            self.category = "خضروات"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🍎 فاكهة", emoji="🍎", style=discord.ButtonStyle.secondary)
    async def cat4(self, i, b):
        try:
            self.category = "فاكهة"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🌍 بلاد", emoji="🌍", style=discord.ButtonStyle.secondary)
    async def cat5(self, i, b):
        try:
            self.category = "بلاد"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🎭 ممثل مصري", emoji="🎭", style=discord.ButtonStyle.secondary)
    async def cat6(self, i, b):
        try:
            self.category = "ممثل مصري"; self.stop()
            await i.response.defer()
        except: pass

    @discord.ui.button(label="🎤 مغني مصري", emoji="🎤", style=discord.ButtonStyle.secondary)
    async def cat7(self, i, b):
        try:
            self.category = "مغني مصري"; self.stop()
            await i.response.defer()
        except: pass

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
