import discord
import asyncio
import dotenv
import os
from discord.ext import commands
from discord import app_commands

dotenv.load_dotenv()

bot = commands.Bot(command_prefix="ac.", intents=discord.Intents.all(), case_insensitive=True)

@bot.event
async def on_ready():
    print("Logged in as", str(bot.user))

async def main():
    await bot.load_extension("jishaku")
    async with bot:
        await bot.start(os.environ["TOKEN"])

asyncio.run(main())
