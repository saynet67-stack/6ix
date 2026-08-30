import discord
from discord.ext import commands
from datetime import timedelta
from moderation.memberutils import resolve_member, extract_rest, parse_minutes_and_reason

class TimeoutCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="تايم", aliases=["ت"])
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, *, args: str = None):
        member = await resolve_member(ctx, args)
        if not member:
            return await ctx.send("❌ **حدد العضو** بالمنشن أو بالرد على رسالته")
        if member.id == ctx.guild.owner_id and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ **لا أستطيع عمل تايم أوت للأونر**")
        if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.guild.me.top_role:
            return await ctx.send(f"❌ **لا أستطيع عمل تايم أوت لـ {member.mention}** — رتبته أعلى مني")
        minutes, reason = parse_minutes_and_reason(extract_rest(args), default_minutes=10)
        try:
            duration = timedelta(minutes=minutes)
            await member.timeout(duration, reason=reason)
            await ctx.send(f"✅ **تم إعطاء تايم أوت لـ {member.mention}** لمدة {minutes} دقائق")
        except discord.Forbidden:
            await ctx.send(f"❌ **ما عندي صلاحية عمل تايم أوت لـ {member.mention}**")
        except Exception as e:
            await ctx.send(f" ❌ **{e}**")

    @timeout.error
    async def timeout_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(" ❌ **ليس لديك صلاحية الـ Moderate Members**")
        else:
            await ctx.send(f" {error}")

async def setup(bot):
    await bot.add_cog(TimeoutCog(bot))