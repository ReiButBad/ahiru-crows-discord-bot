import dotenv
dotenv.load_dotenv()

import discord
import asyncio
import os
import traceback
import surrealdb
from discord.ext import commands
from lib.constants import target_guild_id
from bot import Bot



bot = Bot(
    command_prefix="ac.",
    intents=discord.Intents.all(),
    case_insensitive=True,
    owner_ids=[int(i.strip()) for i in os.environ["OWNER_IDS"].split(",")],
)
bot.error_report_id = os.environ["ERROR_REPORT_ID"]
roles = os.getenv("HELPER_ROLES")
if roles is not None:
    bot.helper_roles = [int(i.strip()) for i in roles.split(",")]

surrealdb_opt = {
    "url": os.environ["SURREALDB_URL"],
    "ns": os.environ["SURREALDB_NS"],
    "db": os.environ["SURREALDB_DB"],
    "user": os.environ["SURREALDB_USER"],
    "pass": os.environ["SURREALDB_PASS"]
}


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: discord.app_commands.AppCommandError
):
    print("".join(traceback.format_exception(type(error), error, error.__traceback__)))

@bot.listen()
async def on_command_error(ctx, error):
    print(traceback.format_exception(type(error), error, error.__traceback__))


@bot.event
async def on_ready():
    print("Logged in as", str(bot.user))


@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    msg = await ctx.reply("Syncing to guild...")
    async with ctx.typing():
        await bot.tree.sync(guild=discord.Object(target_guild_id))
        await msg.edit(content="Successfully synced!")

async def main():
    await bot.load_extension("jishaku")

    extensions = os.getenv("EXTENSIONS") or []
    for i in extensions.split(","):
        await bot.load_extension(f"extensions.{i.strip()}")

    async with bot, surrealdb.Surreal(surrealdb_opt["url"]) as db:
        await db.use(surrealdb_opt["ns"], surrealdb_opt["db"])
        await db.signin({"user": surrealdb_opt["user"], "pass": surrealdb_opt["pass"]})
        bot.db = db
        await bot.start(os.environ["TOKEN"])


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("SIGINT received")
except:
    raise