import os
from discord import Interaction
from discord.ext import commands
from bot import Bot
from .constants import roles, positions_type


async def is_helper(interaction: Interaction[Bot]):
    return any([i.id in interaction.client.helper_roles for i in interaction.user.roles])


def positions_to_roles(pos_list: list[positions_type]):
    return [roles.get(i) for i in pos_list]


def format_roles(roles: list[int]):
    return ", ".join([f"<@&{i}>" for i in roles if i is not None])


async def is_owner(interaction: Interaction[commands.Bot]):
    return await interaction.client.is_owner(interaction.user)
