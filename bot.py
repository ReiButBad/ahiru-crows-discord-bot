from typing import Optional
from discord.ext import commands
from surrealdb import Surreal


class Bot(commands.Bot):
    db: Optional[Surreal]
    error_report_id: int
    helper_roles: list[int]
