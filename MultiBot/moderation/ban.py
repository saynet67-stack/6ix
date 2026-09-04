import discord
import asyncio
from datetime import timedelta
from discord.ext import commands
from moderation.memberutils import resolve_member, extract_rest, parse_minutes_and_reason

class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="يكسمك", aliases=["بان", "ban", "حظر"])
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def ban(self, ctx, *, args: str = None):
        member = await resolve_member(ctx, args)
        if not member:
            return await ctx.send("❌ **حدد العضو** بالمنشن أو بالرد على رسالته")
        minutes, reason = parse_minutes_and_reason(extract_rest(args))
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send(" البوت ليس لديه صلاحية الحظر")
        await member.ban(reason=reason)
        if minutes > 0:
            await ctx.send(f"🚫 **تم حظر {member.mention}** {minutes} دقيقة ({reason or 'بلا سبب'})")
            await asyncio.sleep(minutes * 60)
            guild = ctx.guild
            try:
                await guild.unban(member, reason="انتهت مدة الحظر")
                await ctx.send(f"✅ **تم فك الحظر عن {member.mention}** تلقائيًا بعد {minutes} دقيقة")
            except Exception as e:
                print(f"[BAN] auto-unban err: {e}")
        else:
            await ctx.send(f"🚫 **تم حظر {member.mention}** بشكل دائم ({reason or 'بلا سبب'})")

    @commands.command(name="المتبندين", aliases=["المحظورين", "banlist", "bans"])
    @commands.has_permissions(ban_members=True)
    async def ban_list(self, ctx):
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send("❌ البوت ليس لديه صلاحية عرض المحظورين")
        
        bans = await ctx.guild.bans()
        if not bans:
            return await ctx.send("✅ **لا يوجد محظورين في السيرفر**")
        
        description = ""
        for i, ban_entry in enumerate(bans, 1):
            user = ban_entry.user
            reason = ban_entry.reason or "بلا سبب"
            description += f"**{i}.** {user.name}#{user.discriminator} - `{reason}`\n"
        
        embed = discord.Embed(
            color=0xed4245,
            title="🚫 قائمة المحظورين",
            description=description
        )
        embed.set_footer(text=f"المجموع: {len(bans)} محظور")
        await ctx.send(embed=embed)

    @commands.command(name="فك", aliases=["unban", "فك_بان"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, number: int):
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send("❌ البوت ليس لديه صلاحية فك الحظر")
        
        bans = await ctx.guild.bans()
        if not bans:
            return await ctx.send("✅ **لا يوجد محظورين في السيرفر**")
        
        if number < 1 or number > len(bans):
            return await ctx.send(f"❌ **الرقم غير صحيح**\nاستخدم `المتبندين` لعرض القائمة")
        
        ban_entry = bans[number - 1]
        user = ban_entry.user
        
        try:
            await ctx.guild.unban(user)
            embed = discord.Embed(
                color=0x57f287,
                title="✅ تم فك الحظر",
                description=f"```css\n{user.name}#{user.discriminator}\n```"
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ **فشل فك الحظر:** `{e}`")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(" معكش  صلاحية البان")
        else:
            await ctx.send(f" {error}")

async def setup(bot):
    await bot.add_cog(BanCog(bot))
