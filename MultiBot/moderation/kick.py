import discord
from discord.ext import commands
from moderation.memberutils import resolve_member, clean_reason

C = 0x2b2d31

class KickCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def e(self, desc):
        return discord.Embed(color=C, description=desc)

    @commands.command(name="برا")
    @commands.has_permissions(kick_members=True)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def kick(self, ctx, *, args: str = None):
        member = await resolve_member(ctx, args)
        if not member:
            return await ctx.send(embed=self.e("❌ **حدد العضو** بالمنشن أو الرد على رسالته"))
        reason = clean_reason(args)
        if reason and "يكسمك" in reason:
            if not ctx.guild.me.guild_permissions.ban_members:
                return await ctx.send(embed=self.e("❌ **ليس لدي صلاحية الحظر**"))
            await member.ban(reason=reason)
            embed = discord.Embed(color=C, title="🚫 تم الحظر")
            embed.add_field(name="العضو", value=member.mention, inline=True)
            if reason: embed.add_field(name="السبب", value=reason, inline=False)
            return await ctx.send(embed=embed)
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.send(embed=self.e("❌ **ليس لدي صلاحية الطرد**"))
        await member.kick(reason=reason)
        embed = discord.Embed(color=C, title="👋 تم الطرد")
        embed.add_field(name="العضو", value=member.mention, inline=True)
        if reason: embed.add_field(name="السبب", value=reason, inline=False)
        embed.set_footer(text=f"بواسطة {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self.e("You don't have kick permission"))
        else:
            await ctx.send(embed=self.e(str(error)))

async def setup(bot):
    await bot.add_cog(KickCog(bot))
