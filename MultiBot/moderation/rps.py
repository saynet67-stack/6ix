import discord
from discord.ext import commands
import random

C = 0x2b2d31

class RPSView(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=30)
        self.player = player
        self.choice = None

    @discord.ui.button(emoji="🪨", style=discord.ButtonStyle.primary)
    async def rock(self, interaction, button):
        self.choice = "rock"
        await self.process_choice(interaction, "🪨 حجر")

    @discord.ui.button(emoji="📄", style=discord.ButtonStyle.primary)
    async def paper(self, interaction, button):
        self.choice = "paper"
        await self.process_choice(interaction, "📄 ورقة")

    @discord.ui.button(emoji="✂️", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction, button):
        self.choice = "scissors"
        await self.process_choice(interaction, "✂️ مقص")

    async def process_choice(self, interaction, player_choice_emoji):
        if interaction.user != self.player:
            return await interaction.response.send_message("❌ **ده مش لعبتك!**", ephemeral=True)

        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        
        bot_emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        bot_choice_emoji = bot_emojis[bot_choice]

        # Determine winner
        if self.choice == bot_choice:
            result = "🤝 **تعادل!**"
            color = 0xfee75c
        elif (self.choice == "rock" and bot_choice == "scissors") or \
             (self.choice == "paper" and bot_choice == "rock") or \
             (self.choice == "scissors" and bot_choice == "paper"):
            result = "🎉 **أنت فزت!**"
            color = 0x57f287
        else:
            result = "😢 **البوت فاز!**"
            color = 0xed4245

        embed = discord.Embed(
            color=color,
            title="🪨 حجر ورقة مقص",
            description=f"```css\nأنت: {player_choice_emoji}\nالبوت: {bot_choice_emoji}\n```\n\n{result}"
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class RPSCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="حجر_ورقة_مقص", aliases=["rps", "ح_و_م"])
    async def rps(self, ctx):
        view = RPSView(ctx.author)
        embed = discord.Embed(
            color=0x9b59b6,
            title="🪨 حجر ورقة مقص",
            description=f"🎯 {ctx.author.mention} اختر حركتك!"
        )
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RPSCog(bot))
