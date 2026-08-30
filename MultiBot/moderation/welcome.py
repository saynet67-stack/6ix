import discord
from discord.ext import commands
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from resources.welcome_card import generate_welcome_card
    HAVE_CARD = True
except Exception:
    HAVE_CARD = False
    generate_welcome_card = None

C = 0x2b2d31
WELCOME_CHANNEL_ID = 1525427063668867124

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_role_id = None

    def e(self, desc):
        return discord.Embed(color=C, description=desc)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        try:
            card = None
            if HAVE_CARD:
                avatar_url = member.display_avatar.with_format("png").url
                server_icon = member.guild.icon.with_format("png").url if member.guild.icon else None
                card = await generate_welcome_card(
                    avatar_url=avatar_url,
                    server_icon_url=server_icon,
                    server_name=member.guild.name,
                    member_name=member.display_name,
                    member_count=member.guild.member_count
                )
            file = discord.File(card, filename="welcome.png") if card else None
        except Exception:
            file = None

        embed = discord.Embed(color=C)
        embed.set_author(
            name=f"مرحباً بك في {member.guild.name}",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )
        embed.description = (
            f"{member.mention} **انضم إلينا!** 🎊\n\n"
            f"• العضو رقم `#{member.guild.member_count}`\n"
            f"• تم إنشاء الحساب: `{member.created_at.strftime('%Y-%m-%d')}`\n\n"
            f"نتمنى لك أوقاتاً جميلة معنا 💫"
        )
        embed.set_footer(
            text=member.guild.name,
            icon_url=member.guild.icon.url if member.guild.icon else None
        )

        try:
            if file:
                await channel.send(file=file, embed=embed)
            else:
                await channel.send(embed=embed)
        except:
            pass

        if self.welcome_role_id:
            role = member.guild.get_role(self.welcome_role_id)
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass

    @commands.command(name="رتبة_ترحيب", aliases=["welcome_role"])
    @commands.has_permissions(administrator=True)
    async def set_welcome_role(self, ctx, role: discord.Role = None):
        if role:
            self.welcome_role_id = role.id
            await ctx.send(embed=self.e(f"✅ **تم تعيين رتبة الترحيب:** {role.mention}"))
        else:
            self.welcome_role_id = None
            await ctx.send(embed=self.e("🗑️ **تم إزالة رتبة الترحيب**"))

    @commands.command(name="شات_ترحيب", aliases=["welcome_channel"])
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx, channel: discord.TextChannel = None):
        global WELCOME_CHANNEL_ID
        ch = channel or ctx.channel
        WELCOME_CHANNEL_ID = ch.id
        await ctx.send(embed=self.e(f"✅ **تم تعيين شات الترحيب:** {ch.mention}"))

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
