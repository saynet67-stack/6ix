import discord
from discord.ext import commands
import asyncio

C = 0x2b2d31

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=86400)

    @discord.ui.button(label="🔒 إغلاق التذكرة", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close_btn(self, interaction, button):
        overwrites = interaction.channel.overwrites
        target = None
        for t, ov in overwrites.items():
            if isinstance(t, discord.Member) and t != interaction.guild.me:
                target = t
                break
        if target:
            await interaction.channel.set_permissions(target, view_channel=False)
        embed = discord.Embed(color=C, description="🔒 **تم إغلاق التذكرة** — سيتم حذف الشات بعد 5 ثوانٍ")
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.category_id = None

    def e(self, desc):
        return discord.Embed(color=C, description=desc)

    async def get_category(self, guild):
        if self.category_id:
            cat = guild.get_channel(self.category_id)
            if cat: return cat
        for ch in guild.channels:
            if isinstance(ch, discord.CategoryChannel) and ch.name == "Tickets":
                self.category_id = ch.id
                return ch
        cat = await guild.create_category("Tickets")
        self.category_id = cat.id
        return cat

    @commands.command(name="تكت", aliases=["ticket", "دعم", "ابلاغ", "تيكت"])
    async def ticket(self, ctx, *, reason="No reason provided"):
        existing = discord.utils.get(ctx.guild.text_channels, name=f"ticket-{ctx.author.name.lower()}")
        if existing:
            return await ctx.send(embed=self.e("❌ **لديك تذكرة مفتوحة بالفعل** — استخدمها بدلاً من إنشاء جديدة"))

        cat = await self.get_category(ctx.guild)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        for role in ctx.guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        ch = await ctx.guild.create_text_channel(
            f"ticket-{ctx.author.name[:20]}",
            category=cat,
            overwrites=overwrites,
            reason=f"Ticket by {ctx.author}"
        )

        embed = discord.Embed(color=C, title="🎫 تذكرة دعم جديدة")
        embed.add_field(name="👤 العضو", value=ctx.author.mention, inline=True)
        embed.add_field(name="📌 السبب", value=reason, inline=False)
        embed.add_field(name="🕐 الوقت", value=f"<t:{int(ctx.message.created_at.timestamp())}:F>", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="اضغط 🔒 للإغلاق عند الانتهاء")
        await ch.send(embed=embed, view=TicketView())
        await ctx.send(embed=self.e(f"✅ **تم إنشاء التذكرة:** {ch.mention}"))

    @ticket.error
    async def ticket_error(self, ctx, error):
        await ctx.send(embed=self.e(str(error)))

    @commands.command(name="قائمة_التكتات", aliases=["tickets", "التكتات"])
    @commands.has_permissions(administrator=True)
    async def list_tickets(self, ctx):
        cat = await self.get_category(ctx.guild)
        tickets = [c for c in cat.text_channels if c.name.startswith("ticket-")]
        if not tickets:
            return await ctx.send(embed=self.e("📭 **لا توجد تذاكر مفتوحة**"))
        embed = discord.Embed(color=C, title=f"📋 التذاكر المفتوحة ({len(tickets)})")
        for t in tickets:
            embed.add_field(name=f"🎫 {t.name}", value=t.mention, inline=False)
        embed.set_footer(text="استخدم 🔒 للإغلاق")
        await ctx.send(embed=embed)

    @commands.command(name="تحديد_تصنيف", aliases=["set_category"])
    @commands.has_permissions(administrator=True)
    async def set_category(self, ctx, category: discord.CategoryChannel = None):
        if category:
            self.category_id = category.id
            await ctx.send(embed=self.e(f"Ticket category set to {category.name}"))
        else:
            cat = await self.get_category(ctx.guild)
            await ctx.send(embed=self.e(f"Ticket category: {cat.mention}"))

async def setup(bot):
    await bot.add_cog(TicketCog(bot))
