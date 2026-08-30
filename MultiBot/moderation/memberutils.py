import discord
import re
from discord.ext import commands

MENTION_RE = re.compile(r"<@!?(\d+)>\s*(.*)$", re.DOTALL)


class AnyMember(commands.Converter):
    """Resolve a member from a mention, raw ID, username, or reply."""

    async def convert(self, ctx, argument):
        member = await resolve_member(ctx, argument)
        if member is None:
            raise commands.BadArgument("Member not found")
        return member


async def resolve_member(ctx, argument=None):
    """Try in order: explicit mention/ID in argument -> message mentions -> reply -> username lookup."""
    if argument:
        m = MENTION_RE.search(argument)
        if m:
            uid = int(m.group(1))
            member = ctx.guild.get_member(uid)
            if member:
                return member
            try:
                return await ctx.guild.fetch_member(uid)
            except discord.HTTPException:
                pass
        if argument.strip().isdigit():
            uid = int(argument.strip())
            member = ctx.guild.get_member(uid)
            if member:
                return member
            try:
                return await ctx.guild.fetch_member(uid)
            except discord.HTTPException:
                pass

    if ctx.message.mentions:
        return ctx.message.mentions[0]

    ref = ctx.message.reference
    if ref and isinstance(ref.resolved, discord.Message):
        return ref.resolved.author

    if argument and argument.strip():
        conv = commands.MemberConverter()
        try:
            return await conv.convert(ctx, argument.strip())
        except commands.BadArgument:
            pass

    return None


def clean_reason(text):
    """Remove @mentions from a reason string."""
    if not text:
        return None
    text = re.sub(r"<@!?\d+>", "", text).strip()
    return text or None


async def fetch_from_raw_mention(guild, message):
    """Resolve the first raw mention ID via get_member/fetch_member (works without Members intent being cached)."""
    if not message.raw_mentions:
        return None
    uid = message.raw_mentions[0]
    member = guild.get_member(uid)
    if member:
        return member
    try:
        return await guild.fetch_member(uid)
    except discord.HTTPException:
        return None


def extract_rest(args):
    """Return the text after the leading member mention, or the whole text if no mention."""
    if not args:
        return None
    m = MENTION_RE.search(args)
    if m:
        return m.group(2).strip() or None
    return args.strip() or None


def parse_minutes_and_reason(text, default_minutes=60):
    """Split '30 سبب ما' into (30, 'سبب ما'). No number -> default minutes."""
    if not text:
        return default_minutes, None
    parts = text.split(maxsplit=1)
    if parts[0].isdigit():
        minutes = int(parts[0])
        reason = parts[1].strip() if len(parts) > 1 else None
    else:
        minutes = default_minutes
        reason = text
    return minutes, clean_reason(reason)