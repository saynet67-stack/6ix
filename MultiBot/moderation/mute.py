import discord
from discord.ext import commands
from datetime import timedelta
from moderation.memberutils import resolve_member, extract_rest, parse_minutes_and_reason

class MuteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_moderate(self, ctx, member):
        if ctx.author.id == ctx.guild.owner_id:
            return True
        if member.top_role >= ctx.guild.me.top_role:
            return False
        return True

    def mod_perms(ctx):
        return ctx.author.guild_permissions.manage_roles or ctx.author.guild_permissions.moderate_members or ctx.author.guild_permissions.administrator

    async def get_muted_role(self, guild):
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                try:
                    await channel.set_permissions(muted_role, speak=False, send_messages=False)
                except:
                    pass
        return muted_role

    @commands.command(name="ا", aliases=["كتم","اكتم","اكتمي","اخرس","اخرسي"])
    @commands.check(mod_perms)
    @commands.cooldown(1, 3, commands.BucketType.member)
    async def mute(self, ctx, *, args: str = None):
        member = await resolve_member(ctx, args)
        if not member:
            return await ctx.send("❌ **حدد العضو** بالمنشن أو بالرد على رسالته")
        if not self.can_moderate(ctx, member):
            return await ctx.send(f"❌ **لا أستطيع كتم {member.mention}** — رتبته أعلى من رتبتي")
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ **لا أستطيع كتم الأونر**")
        minutes, reason = parse_minutes_and_reason(extract_rest(args))
        done = []
        # 1) Apply Muted role first (always works if bot has manage_roles)
        try:
            muted_role = await self.get_muted_role(ctx.guild)
            if muted_role not in member.roles:
                await member.add_roles(muted_role, reason=reason)
            done.append("رول Muted")
        except discord.Forbidden:
            pass
        except Exception as e:
            return await ctx.send(f"❌ **{e}**")
        # 2) Also apply timeout if possible
        if minutes > 0 and ctx.guild.me.guild_permissions.moderate_members:
            try:
                duration = timedelta(minutes=minutes)
                await member.timeout(duration, reason=reason)
                done.append("تايم أوت")
            except discord.Forbidden:
                pass
            except Exception as e:
                await ctx.send(f"❌ **{e}**")
        if not done:
            return await ctx.send(f"❌ **ما عندي صلاحية كتم {member.mention}**")
        return await ctx.send(f"✅ **تم كتم {member.mention}** لمدة {minutes} دقيقة ({' + '.join(done)})")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(" ❌ **ليس لديك صلاحية الإدارة**")
        elif isinstance(error, commands.CommandOnCooldown):
            return
        else:
            await ctx.send(f" {error}")

async def setup(bot):
    await bot.add_cog(MuteCog(bot))