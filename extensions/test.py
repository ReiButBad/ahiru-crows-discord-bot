from discord.ext import commands
from discord import app_commands

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def ping(self, interaction):
        await interaction.response.send_message(f"pong {interaction.user}")

async def setup(bot):
    await bot.add_cog(TestCog(bot))
