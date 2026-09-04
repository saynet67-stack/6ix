import discord
from discord.ext import commands
import random

C = 0x2b2d31

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction):
        view = self.view
        if view.board[self.x][self.y] != " ":
            return await interaction.response.send_message("❌ **المكان مشغول!**", ephemeral=True)

        if view.current_player == view.player1:
            self.label = "X"
            self.style = discord.ButtonStyle.danger
            view.board[self.x][self.y] = "X"
            view.current_player = view.player2
        else:
            self.label = "O"
            self.style = discord.ButtonStyle.success
            view.board[self.x][self.y] = "O"
            view.current_player = view.player1

        await interaction.response.edit_message(view=view)

        winner = view.check_winner()
        if winner:
            if winner == "X":
                await interaction.followup.send(embed=discord.Embed(color=0x57f287, description=f"🎉 **{view.player1.mention} فاز!**"))
            elif winner == "O":
                await interaction.followup.send(embed=discord.Embed(color=0x57f287, description=f"🎉 **{view.player2.mention} فاز!**"))
            else:
                await interaction.followup.send(embed=discord.Embed(color=0xfee75c, description="🤝 **تعادل!**"))
            view.stop()

class TicTacToeView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.board = [[" " for _ in range(3)] for _ in range(3)]

        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y, " "))

    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != " ":
                return row[0]
        # Check columns
        for x in range(3):
            if self.board[0][x] == self.board[1][x] == self.board[2][x] != " ":
                return self.board[0][x]
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != " ":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != " ":
            return self.board[0][2]
        # Check draw
        if all(cell != " " for row in self.board for cell in row):
            return "draw"
        return None

class TicTacToeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.command(name="تكتاك_تو", aliases=["اكس_او", "xo"])
    async def tictactoe(self, ctx, opponent: discord.Member = None):
        if ctx.channel.id in self.active_games:
            return await ctx.send(embed=discord.Embed(color=0xed4245, description="❌ **في لعبة شغالة في الشات دا**"))

        if not opponent:
            return await ctx.send(embed=discord.Embed(color=0xed4245, description="❌ **استخدم:** `تكتاك_تو @اللاعب`"))

        if opponent.bot:
            return await ctx.send(embed=discord.Embed(color=0xed4245, description="❌ **ما يقدرش يلعب ضد بوت**"))

        if opponent == ctx.author:
            return await ctx.send(embed=discord.Embed(color=0xed4245, description="❌ **ما يقدرش يلعب ضد نفسه**"))

        self.active_games[ctx.channel.id] = True
        view = TicTacToeView(ctx.author, opponent)

        embed = discord.Embed(
            color=0x9b59b6,
            title="❌ لعبة تكتاك تو",
            description=f"```css\n{ctx.author.name} (X) vs {opponent.name} (O)\n```\n\n🎯 **الدور:** {ctx.author.mention}"
        )
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()
        self.active_games.pop(ctx.channel.id, None)

async def setup(bot):
    await bot.add_cog(TicTacToeCog(bot))
