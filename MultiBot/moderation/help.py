import discord
from discord.ext import commands

C = 0x2b2d31

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="اوامر", aliases=["مساعدة", "help"])
    async def help_command(self, ctx):
        if self.bot.number != 1:
            return

        embed = discord.Embed(
            color=0x5865f2,
            title="📚 قائمة الأوامر",
            description="**مرحباً! إليك جميع الأوامر المتاحة:**"
        )

        embed.add_field(
            name="🎵 **الموسيقى**",
            value="```css\nش - شغل أغنية\nتوقف - إيقاف الموسيقى\nالتالي - الأغنية التالية\nالسابق - الأغنية السابقة\nقائمة - قائمة التشغيل\nكلمات - كلمات الأغنية```",
            inline=False
        )

        embed.add_field(
            name="🏠 **الروم المؤقت**",
            value="```css\nافتح فويس - إنشاء روم مؤقت\nاسم رومي - تغيير اسم الروم\nحد رومي - تعيين حد اللاعبين\nقفل رومي - قفل الروم\nفتح رومي - فتح الروم\nاقفل الفويس - حذف الروم```",
            inline=False
        )

        embed.add_field(
            name="🔨 **الموديريشن**",
            value="```css\nبان - حظر عضو\nكيك - طرد عضو\nميوت - كتم عضو\nتايم آوت - إيقاف مؤقت\nقفل - قفل الشات\nفتح - فتح الشات```",
            inline=False
        )

        embed.add_field(
            name="🎮 **الألعاب**",
            value="```css\nالعاب - عرض أوامر الألعاب\nلعبة - لعبة Heads Up\nتريفيا - أسئلة عامة\nتكتاك_تو - لعبة X O\nحجر_ورقة_مقص - لعبة حجر ورقة مقص```",
            inline=False
        )

        embed.add_field(
            name="🎫 **التذاكر**",
            value="```css\nتذكرة - إنشاء تذكرة\nإغلاق - إغلاق التذكرة```",
            inline=False
        )

        embed.set_footer(text="💡 اكتب `العاب` لعرض أوامر الألعاب بالتفصيل")
        await ctx.send(embed=embed)

    @commands.command(name="العاب", aliases=["ألعاب", "games"])
    async def games_command(self, ctx):
        if self.bot.number != 1:
            return

        embed = discord.Embed(
            color=0x9b59b6,
            title="🎮 أوامر الألعاب",
            description="**مرحباً! إليك جميع الألعاب المتاحة:**"
        )

        embed.add_field(
            name="🧠 **لعبة Heads Up**",
            value="```css\nلعبة - بدء اللعبة\n```\n📝 **الوصف:** لعبة تخمين الكلمات مع الفرق\n🎯 **الأقسام:** كرة، مشاهير، خضروات، فاكهة، بلاد، ممثل مصري، مغني مصري",
            inline=False
        )

        embed.add_field(
            name="❓ **لعبة Trivia**",
            value="```css\nتريفيا - بدء اللعبة\nسؤال - سؤال واحد\n```\n📝 **الوصف:** 16 سؤال متنوع: جغرافيا، تاريخ، علم، رياضة\n⏱️ **الوقت:** 15 ثانية للإجابة",
            inline=False
        )

        embed.add_field(
            name="❌ **لعبة Tic Tac Toe**",
            value="```css\ntكتاك_تو - بدء اللعبة\nاكس_او - بدء اللعبة\nxo - بدء اللعبة\n```\n📝 **الوصف:** العب ضد لاعب آخر\n🎯 **الاستخدام:** `تكتاك_تو @اللاعب`",
            inline=False
        )

        embed.add_field(
            name="🪨 **لعبة Rock Paper Scissors**",
            value="```css\nحجر_ورقة_مقص - بدء اللعبة\nrps - بدء اللعبة\nح_و_م - بدء اللعبة\n```\n📝 **الوصف:** العب ضد البوت\n🎯 **الخيارات:** حجر، ورقة، أو مقص",
            inline=False
        )

        embed.set_footer(text="💡 اكتب `اوامر` لعرض جميع الأوامر")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
