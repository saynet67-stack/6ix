import discord
from discord.ext import commands
import random

C = 0x2b2d31

TRIVIA_QUESTIONS = [
    {"q": "ما هي عاصمة مصر؟", "a": ["القاهرة", "Cairo"], "correct": "القاهرة"},
    {"q": "ما هو أكبر كوكب في المجموعة الشمسية؟", "a": ["المشتري", "Jupiter"], "correct": "المشتري"},
    {"q": "كم عدد قارات العالم؟", "a": ["7", "سبعة"], "correct": "7"},
    {"q": "من هو مؤسس شركة مايكروسوفت؟", "a": ["بيل غيتس", "Bill Gates"], "correct": "بيل غيتس"},
    {"q": "ما هي العملة المستخدمة في اليابان؟", "a": ["الين", "Yen"], "correct": "الين"},
    {"q": "في أي سنة هبط الإنسان على القمر؟", "a": ["1969"], "correct": "1969"},
    {"q": "ما هو أسرع حيوان بري؟", "a": ["الفهد", "الشيتا"], "correct": "الفهد"},
    {"q": "كم عدد لاعبي فريق كرة القدم؟", "a": ["11"], "correct": "11"},
    {"q": "ما هي أكبر دولة في العالم من حيث المساحة؟", "a": ["روسيا", "Russia"], "correct": "روسيا"},
    {"q": "من هو كاتب رواية هاري بوتر؟", "a": ["جي كي رولينغ", "J.K. Rowling"], "correct": "جي كي رولينغ"},
    {"q": "ما هو العنصر الكيميائي الذي رمزه O؟", "a": ["الأكسجين", "Oxygen"], "correct": "الأكسجين"},
    {"q": "كم عدد ألوان قوس قزح؟", "a": ["7"], "correct": "7"},
    {"q": "ما هي عاصمة فرنسا؟", "a": ["باريس", "Paris"], "correct": "باريس"},
    {"q": "من هو رسول الإسلام؟", "a": ["محمد", "النبي محمد"], "correct": "محمد"},
    {"q": "ما هو أطول نهر في العالم؟", "a": ["النيل", "نهر النيل"], "correct": "النيل"},
]

class TriviaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command(name="تريفيا", aliases=["سؤال", "أسئلة"])
    async def trivia(self, ctx):
        if ctx.channel.id in self.active_games:
            return await ctx.send(embed=discord.Embed(color=0xed4245, description="❌ **في لعبة شغالة في الشات دا**"))

        question = random.choice(TRIVIA_QUESTIONS)
        self.active_games[ctx.channel.id] = question

        embed = discord.Embed(
            color=0x9b59b6,
            title="🧠 لعبة الأسئلة",
            description=f"```css\n{question['q']}\n```\n\n⏱️ **لديك 15 ثانية للإجابة!**"
        )
        embed.set_footer(text="💡 اكتب إجابتك في الشات")
        msg = await ctx.send(embed=embed)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            response = await self.bot.wait_for("message", check=check, timeout=15)
        except:
            del self.active_games[ctx.channel.id]
            return await ctx.send(embed=discord.Embed(color=0xed4245, description=f"⏰ **انتهى الوقت!**\n\n✅ **الإجابة الصحيحة:** `{question['correct']}`"))

        user_answer = response.content.strip().lower()
        correct_answers = [a.lower() for a in question["a"]]

        if user_answer in correct_answers:
            del self.active_games[ctx.channel.id]
            await ctx.send(embed=discord.Embed(color=0x57f287, description=f"🎉 **إجابة صحيحة!**\n\n✅ **الإجابة:** `{question['correct']}`"))
        else:
            del self.active_games[ctx.channel.id]
            await ctx.send(embed=discord.Embed(color=0xed4245, description=f"😢 **إجابة خاطئة!**\n\n✅ **الإجابة الصحيحة:** `{question['correct']}`"))

async def setup(bot):
    await bot.add_cog(TriviaCog(bot))
