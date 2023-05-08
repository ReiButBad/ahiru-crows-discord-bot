import discord
import os
from typing import Literal

tryout_score_channel_id: int = int(os.environ["CHANNEL"])
target_guild_id: int = int(os.environ["GUILD"])


class RblxUrl:
    user_by_username = "https://users.roblox.com/v1/usernames/users"
    avatar_headshot = "https://thumbnails.roblox.com/v1/users/avatar-headshot"
    user_by_id = "https://users.roblox.com/v1/users/"


positions_type = Literal[
    "Setter",
    "Libero",
    "Middle Blocker",
    "Outside Hitter",
    "Opposite Hitter",
    "All Rounder",
]
main_positions_type = Literal[
    "Setter", "Libero", "Middle Blocker", "Outside Hitter", "Opposite Hitter"
]

positions = {
    "Middle Blocker",
    "Setter",
    "Outside Hitter",
    "Opposite Hitter",
    "Libero",
    "All Rounder",
}

# right br 1092378775003615302
# left br 1092378767894253568
roles = {
    "Pinch Server": 1104424737460994100,
    "Middle Blocker": 1104016343218532372,
    "Libero": 1092378776568090664,
    "All Rounder": 1075333624016162897,
    "Setter": 1075333620849459280,
    "Outside Hitter": 1075333618928451604,
    "Opposite Hitter": 1075333616827125790,
}

strings = {1: 1075333612079153152, 2: 1075333613614280704, 3: 1075333615161974784}


class Color:
    success = discord.Color.from_rgb(104, 194, 25)
    failed = discord.Color.from_rgb(194, 37, 23)
    pending = discord.Color.from_rgb(201, 133, 16)
