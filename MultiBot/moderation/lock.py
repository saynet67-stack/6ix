import discord
from discord.ext import commands

C = 0x2b2d31

class LockCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def e(self, desc):
        return discord.Embed(color=C, description=desc)

    @commands.group(name="قفل", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        try:
            channel = channel or ctx.channel
            everyone = ctx.guild.default_role
            overwrite = channel.overwrites_for(everyone)
            overwrite.send_messages = False
            await channel.set_permissions(everyone, overwrite=overwrite)
            await ctx.send(embed=self.e(f"Locked {channel.mention}"))
        except Exception as e:
            await ctx.send(embed=self.e(f"Error: {e}"))

    @lock.command(name="رومي")
    async def lock_room(self, ctx):
        mc = self.bot.get_cog("TempVoice")
        if mc and hasattr(mc, "lock_room"):
            await mc.lock_room(ctx)
        else:
            await ctx.send(embed=self.e("❌ **الفويسات المؤقتة غير متاحة**"))

    @commands.group(name="فتح", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        try:
            channel = channel or ctx.channel
            everyone = ctx.guild.default_role
            overwrite = channel.overwrites_for(everyone)
            overwrite.send_messages = None
            await channel.set_permissions(everyone, overwrite=overwrite)
            await ctx.send(embed=self.e(f"Unlocked {channel.mention}"))
        except Exception as e:
            await ctx.send(embed=self.e(f"Error: {e}"))

    @unlock.command(name="رومي")
    async def unlock_room(self, ctx):
        mc = self.bot.get_cog("TempVoice")
        if mc and hasattr(mc, "unlock_room"):
            await mc.unlock_room(ctx)
        else:
            await ctx.send(embed=self.e("❌ **الفويسات المؤقتة غير متاحة**"))

async def setup(bot):
    await bot.add_cog(LockCog(bot))
