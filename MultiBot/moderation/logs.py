import discord
from discord.ext import commands
import json
import os
import asyncio

C = 0x2b2d31
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "logs_config.json")

# القنوات الافتراضية — ممكن تتعدل تحت السيرفر نفسه
DEFAULT_CHANNELS = {
    "voice": 1539477670981795840,
    "edit": 1539477708717686785,
    "delete": 1539477909587370054,
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(data):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    def guild_channels(self, guild_id):
        cfg = self.config.get(str(guild_id), {})
        out = {}
        for key, cid in cfg.items():
            ch = self.bot.get_channel(int(cid)) if cid else None
            if ch:
                out[key] = ch.id
        return out

    def log_channel(self, guild_id, category):
        chs = self.guild_channels(guild_id)
        cid = chs.get(category) or chs.get("main") or DEFAULT_CHANNELS.get(category) or DEFAULT_CHANNELS.get("main")
        return self.bot.get_channel(int(cid)) if cid else None

    def e(self, desc, color=C):
        return discord.Embed(color=color, description=desc)

    @commands.command(name="سجل_شات", aliases=["logs_channel", "logchannel"])
    @commands.has_permissions(administrator=True)
    async def set_logs_channel(self, ctx, channel: discord.TextChannel = None):
        ch = channel or ctx.channel
        self.config.setdefault(str(ctx.guild.id), {})["main"] = ch.id
        save_config(self.config)
        await ctx.send(embed=self.e(f"✅ **تم تعيين الشات الرئيسي للسجلات:** {ch.mention}"))

    @commands.command(name="سجل_فويس", aliases=["logs_voice"])
    @commands.has_permissions(administrator=True)
    async def set_logs_voice(self, ctx, channel: discord.TextChannel = None):
        ch = channel or ctx.channel
        self.config.setdefault(str(ctx.guild.id), {})["voice"] = ch.id
        save_config(self.config)
        await ctx.send(embed=self.e(f"✅ **تم تعيين شات سجلات الفويس:** {ch.mention}"))

    @commands.command(name="سجل_تعديل", aliases=["logs_edit"])
    @commands.has_permissions(administrator=True)
    async def set_logs_edit(self, ctx, channel: discord.TextChannel = None):
        ch = channel or ctx.channel
        self.config.setdefault(str(ctx.guild.id), {})["edit"] = ch.id
        save_config(self.config)
        await ctx.send(embed=self.e(f"✅ **تم تعيين شات سجلات التعديل:** {ch.mention}"))

    @commands.command(name="سجل_حذف", aliases=["logs_delete"])
    @commands.has_permissions(administrator=True)
    async def set_logs_delete(self, ctx, channel: discord.TextChannel = None):
        ch = channel or ctx.channel
        self.config.setdefault(str(ctx.guild.id), {})["delete"] = ch.id
        save_config(self.config)
        await ctx.send(embed=self.e(f"✅ **تم تعيين شات سجلات الحذف:** {ch.mention}"))

    @commands.command(name="الغاء_تسجيل", aliases=["remove_logs"])
    @commands.has_permissions(administrator=True)
    async def remove_logs(self, ctx):
        self.config.pop(str(ctx.guild.id), None)
        save_config(self.config)
        await ctx.send(embed=self.e("🗑️ **تم إلغاء تسجيل الأحداث في السيرفر ده**"))

    async def _send(self, guild, embed, category="main"):
        ch = self.log_channel(guild.id, category)
        if not ch:
            return
        try:
            await ch.send(embed=embed)
        except Exception:
            pass

    def _author(self, embed, member):
        embed.set_author(
            name=f"{member}",
            icon_url=member.display_avatar.with_format("png").url
        )
        return embed

    # ── الرسائل ──
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        guild = message.guild
        if not guild:
            return
        embed = discord.Embed(color=0xE74C3C, description=(
            f"🗑️ **رسالة محذوفة**\n"
            f"{message.author.mention} في {message.channel.mention}"
        ))
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.with_format("png").url)
        if message.content:
            embed.add_field(name="المحتوى", value=message.content[:1500] or "—", inline=False)
        if message.attachments:
            embed.add_field(name="مرفقات", value="\n".join(a.url for a in message.attachments[:5]), inline=False)
        embed.set_footer(text=f"ID: {message.id}")
        await self._send(guild, embed, "delete")

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        guild = messages[0].guild if messages else None
        if not guild:
            return
        embed = discord.Embed(color=0xE74C3C, description=f"🚮 **تم مسح {len(messages)} رسالة** — {messages[0].channel.mention}")
        await self._send(guild, embed, "delete")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return
        if before.content == after.content:
            return
        guild = before.guild
        if not guild:
            return
        embed = discord.Embed(color=0xF1C40F, description=(
            f"✏️ **رسالة معدلة**\n"
            f"{before.author.mention} في {before.channel.mention} — [الرسالة]({after.jump_url})"
        ))
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.with_format("png").url)
        embed.add_field(name="قبل", value=before.content[:1000] or "—", inline=False)
        embed.add_field(name="بعد", value=after.content[:1000] or "—", inline=False)
        embed.set_footer(text=f"ID: {before.id}")
        await self._send(guild, embed, "edit")

    # ── الأعضاء ──
    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        embed = discord.Embed(color=0x2ECC71, description=(
            f"🟢 **عضو انضم**\n{member.mention} — العضو رقم `#{member.guild.member_count}`\n"
            f"📅 الحساب: `{member.created_at.strftime('%Y-%m-%d')}`"
        ))
        embed.set_author(name=str(member), icon_url=member.display_avatar.with_format("png").url)
        await self._send(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot:
            return
        embed = discord.Embed(color=0xE74C3C, description=(
            f"🔴 **عضو غادر**\n{member.mention} / {member}"
        ))
        embed.set_author(name=str(member), icon_url=member.display_avatar.with_format("png").url)
        await self._send(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(color=0xE74C3C, description=f"🔨 **تم حظر** `{user}` (فاليد {user.id})")
        embed.set_author(name=str(user), icon_url=user.display_avatar.with_format("png").url)
        await self._send(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(color=0x2ECC71, description=f"♻️ **تم فك الحظر** `{user}` (فاليد {user.id})")
        embed.set_author(name=str(user), icon_url=user.display_avatar.with_format("png").url)
        await self._send(guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot:
            return
        if before.nick != after.nick:
            old = before.nick or before.name
            new = after.nick or after.name
            embed = discord.Embed(color=0x3498DB, description=(
                f"🏷️ **تغيير Nickname**\n{after.mention}\n"
                f"`{old}` → `{new}`"
            ))
            embed.set_author(name=str(after), icon_url=after.display_avatar.with_format("png").url)
            await self._send(after.guild, embed)

    # ── الفويس ──
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        guild = member.guild
        if before.channel != after.channel:
            parts = []
            if before.channel:
                parts.append(f"📤 خرج من {before.channel.mention}")
            if after.channel:
                parts.append(f"📥 دخل إلى {after.channel.mention}")
            if parts:
                embed = discord.Embed(color=0x9B59B6, description=f"{member.mention}\n" + "\n".join(parts))
                embed.set_author(name=str(member), icon_url=member.display_avatar.with_format("png").url)
                await self._send(guild, embed, "voice")

async def setup(bot):
    await bot.add_cog(LogsCog(bot))