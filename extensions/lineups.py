import traceback
import discord
import traceback
from aiohttp import ClientSession
from typing import Literal, Optional, Union
from discord.ext import commands
from discord import app_commands, Interaction
from bot import Bot
from lib.constants import (
    roles,
    positions,
    Color,
    RblxUrl,
    positions_type,
    main_positions_type,
)
from lib.utils import positions_to_roles, format_roles, is_helper


class EditPositionsView(discord.ui.View):
    def __init__(
        self,
        user: Union[discord.User, discord.Member],
        positions: list[positions_type],
        playing_position: main_positions_type,
        embed: discord.Embed,
    ):
        self.user = user
        self.positions = positions
        self.playing_position = playing_position
        self.embed = embed
        self.state = None
        super().__init__()

    async def interaction_check(self, interaction: Interaction):
        if self.user.id == interaction.user.id:
            return True

        await interaction.response.send_message(
            "This is not your interaction", ephemeral=True
        )
        return False

    async def on_error(
        self, interaction: Interaction, error: Exception, item: discord.ui.Item
    ):
        print(
            "".join(traceback.format_exception(type(error), error, error.__traceback__))
        )

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="Positions",
        options=[discord.SelectOption(label=i) for i in positions],
    )
    async def select_positions(
        self, interaction: Interaction, select: discord.ui.Select
    ):
        if select.values[0] not in self.positions:
            self.positions.append(select.values[0])
        else:
            if select.values[0] == self.playing_position:
                await interaction.response.send_message(
                    "Cannot remove position that's set to 'playing-position' (wouldnt make sense if a person is Setter but their positions has anything but a Setter position)",
                    ephemeral=True,
                )
                return
            self.positions.remove(select.values[0])

        self.embed.description = "Positions: {0}".format(
            format_roles(positions_to_roles(self.positions))
        )
        await interaction.response.edit_message(view=self, embed=self.embed)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.success)
    async def button_done(self, interaction: Interaction, btn: discord.ui.Button):
        self.stop()

        self.button_done.disabled = True
        self.select_positions.disabled = True
        self.state = True

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def button_cancel(self, interaction: Interaction, btn: discord.ui.Button):
        self.stop()

        self.button_done.disabled = True
        self.select_positions.disabled = True
        self.state = False


@app_commands.guilds(1075042659384705075)
class Lineup(commands.GroupCog):
    pass

    def __init__(self, bot: Bot):
        self.bot = bot
        self.http_session = ClientSession()

    async def get_user_by_name(self, username: str):
        async with self.http_session.post(
            RblxUrl.user_by_username,
            json={"usernames": [username], "excludeBannedUsers": False},
        ) as response:
            data = (await response.json())["data"]
            return data[0] if len(data) > 0 else None

    async def get_avatar_from_id(
        self, id: int, size: Optional[str] = "100x100", format: str = "png"
    ):
        async with self.http_session.get(
            RblxUrl.avatar_headshot,
            params={
                "userIds": [id],
                "size": size,
                "format": "png",
            },
        ) as response:
            data = (await response.json())["data"]
            return data[0]["imageUrl"] if len(data) > 0 else None

    async def get_user_by_id(self, id: int):
        async with self.http_session.get(f"{RblxUrl.user_by_id}/{id}") as response:
            if response.status == 404:
                return None
            return await response.json()

    async def cog_unload(self):
        await self.http_session.close()

    @app_commands.command()
    async def list(self, interaction: Interaction, roster: Literal["main", "sub"]):
        """
        Sends a list of people in the lineup with their positions

            Parameters
            -----------
            roster:
                the roster to select for lineup
        """
        await interaction.response.defer()
        users: list = (
            await self.bot.db.query(
                """
                SELECT *, meta::id(id) AS id FROM players WHERE roster = $roster
            """,
                {"roster": roster},
            )
        )[0]["result"]
        listed = {i: [] for i in positions}
        listed.pop("All Rounder")
        for user in users:
            listed[user["playing_position"]].append(user)
        embed = discord.Embed(
            title=f"{roster.capitalize()} roster players", color=discord.Color.random()
        )
        for pos in listed.items():
            embed.add_field(
                name=f"{pos[0]}s",
                value=", ".join(
                    [
                        "<@!{0}> **({1})**".format(a["id"], a["jersey"] or "N/A")
                        for a in pos[1]
                    ]
                ),
            )
        await interaction.followup.send(embed=embed)

    @app_commands.command()
    @app_commands.check(is_helper)
    @app_commands.rename(playing_position="playing-position")
    @app_commands.rename(ign="ingame-username")
    async def add(
        self,
        interaction: Interaction,
        member: discord.Member,
        roster: Literal["main", "sub"],
        playing_position: main_positions_type,
        ign: str,
        jersey: Optional[app_commands.Range[int, 1, 50]] = None,
    ):
        """
        Adds a member to lineup

            Parameters
            -----------
            member:
                the member to add
            roster:
                the member's roster
            playing_position:
                the member's main position, they can have multiple positions but only 1 playing position
            ingame-username:
                the member's Roblox username (not display name)
            jersey:
                the member's jersey number
        """
        await interaction.response.defer()
        result = await self.bot.db.query(
            f"""
            SELECT * FROM players:{member.id};

            SELECT 1 FROM players WHERE jersey = {jersey};
        """
        )
        if len(result[1]["result"]) == 1:
            return await interaction.followup.send(
                f"Jersey number {jersey} is already taken"
            )
        result = result[0]["result"][0] if len(result[0]["result"]) == 1 else None
        if result is not None:
            return await interaction.followup.send(
                "This person is already in the lineup, maybe you want to edit this person's info? in that case use the `lineup edit` command"
            )

        rblx_user = await self.get_user_by_name(ign)
        if rblx_user is None:
            return await interaction.followup.send(
                f"Cannot find Roblox user by the name of `{ign}`"
            )

        embed = discord.Embed(
            title="Select member positions",
            description=f"Positions: <@&{roles[playing_position]}>",
            color=Color.pending,
        )
        embed.set_footer(
            text="cannot remove position that is set to 'playing-position'"
        )
        embed.add_field(
            name="Playing position & Jersey number",
            value=f"<@&{roles[playing_position]}> ({jersey})",
            inline=False,
        )
        embed.add_field(name="Roster", value=roster.capitalize(), inline=False)
        embed.add_field(
            name="User info",
            value=f"User: {member.mention}\nRoblox account: {rblx_user['name']}",
            inline=False,
        )
        embed.set_thumbnail(url=await self.get_avatar_from_id(rblx_user["id"]))
        view = EditPositionsView(
            interaction.user, [playing_position], playing_position, embed
        )
        msg = await interaction.followup.send(embed=embed, view=view, wait=True)
        timed_out = await view.wait()
        if timed_out or view.state == False:
            return await msg.edit(
                embed=discord.Embed(title="Cancelled", color=Color.failed), view=None
            )

        try:
            await self.bot.db.create(
                f"players:{member.id}",
                {
                    "rblx_id": rblx_user["id"],
                    "positions": view.positions,
                    "playing_position": playing_position,
                    "roster": roster,
                    "jersey": jersey,
                },
            )
        except Exception as e:
            await self.bot.get_user(self.bot.error_report_id).send(
                "".join(traceback.format_exception(type(e), e, e.__traceback__))
            )
            return await msg.edit(
                embed=discord.Embed(
                    title="Something went wrong!",
                    description="this issue is already sent to Rei",
                    color=Color.failed,
                )
            )

        embed.set_footer(text="Successfully added to lineup")
        embed.title = "New member added to lineup"
        embed.color = Color.success
        await msg.edit(embed=embed, view=None)

    @app_commands.command()
    @app_commands.check(is_helper)
    @app_commands.rename(playing_position="playing-position")
    @app_commands.rename(ign="ingame-username")
    async def edit(
        self,
        interaction: Interaction,
        member: discord.Member,
        roster: Optional[Literal["main", "sub"]] = None,
        playing_position: Optional[main_positions_type] = None,
        ign: Optional[str] = None,
        jersey: Optional[app_commands.Range[int, 1, 50]] = None,
    ):
        """
        Edit a member lineup info

            Parameters
            -----------
            member:
                the member to edit
            roster:
                the member's new roster
            playing_position:
                the member's new main position, they can have multiple positions but only 1 playing position
            ingame-username:
                the member's new Roblox username (not display name)
            jersey:
                the member's new jersey number
        """
        await interaction.response.defer()
        result = await self.bot.db.query(
            f"""
            SELECT * FROM players:{member.id};

            SELECT 1 FROM players WHERE jersey = {jersey};
        """
        )
        if len(result[1]["result"]) == 1:
            return await interaction.followup.send(
                f"Jersey number {jersey} is already taken"
            )
        result = result[0]["result"][0] if len(result[0]["result"]) == 1 else None
        if result is None:
            return await interaction.followup.send(
                "This person is not in the lineup, maybe you want to ad this person? in that case use the `lineup add` command"
            )

        playing_position: positions_type = (
            playing_position or result["playing_position"]
        )
        roster: str = roster or result["roster"]
        user_positions: list[positions_type] = result["positions"]
        old_ign = await self.get_user_by_id(result["rblx_id"])

        if ign is not None:
            rblx_user = await self.get_user_by_name(ign)
        else:
            rblx_user = old_ign
        if rblx_user is None:
            return await interaction.followup.send(
                f"Cannot find Roblox user by the name of `{ign}`"
            )

        if playing_position not in user_positions:
            user_positions.append(playing_position)

        embed = discord.Embed(
            title="Select member positions",
            description="Positions: {0}".format(
                format_roles(positions_to_roles(user_positions))
            ),
            color=Color.pending,
        )
        embed.set_footer(
            text="cannot remove position that is set to 'playing-position'"
        )
        embed.add_field(
            name="Playing position & Jersey number",
            value=f"<@&{roles[playing_position]}> ({(jersey or result['jersey']) or 'N/A'})",
            inline=False,
        )
        embed.add_field(name="Roster", value=roster.capitalize(), inline=False)
        embed.add_field(
            name="User info",
            value=f"User: {member.mention}"
            + (
                f"\nOld Roblox account: {old_ign['name'] if old_ign is not None else '**N/A**'}\nNew Roblox account: {rblx_user['name']}"
                if ign is not None
                else ""
            ),
            inline=False,
        )
        embed.set_thumbnail(url=await self.get_avatar_from_id(rblx_user["id"]))
        view = EditPositionsView(
            interaction.user, user_positions, playing_position, embed
        )
        msg = await interaction.followup.send(embed=embed, view=view, wait=True)
        timed_out = await view.wait()
        if timed_out or view.state == False:
            return await msg.edit(
                embed=discord.Embed(title="Cancelled", color=Color.failed), view=None
            )

        try:
            await self.bot.db.update(
                f"players:{member.id}",
                {
                    "rblx_id": rblx_user["id"],
                    "positions": view.positions,
                    "playing_position": playing_position,
                    "roster": roster,
                    "jersey": jersey or result["jersey"],
                },
            )
        except Exception as e:
            await self.bot.get_user(self.bot.error_report_id).send(
                "".join(traceback.format_exception(type(e), e, e.__traceback__))
            )
            return await msg.edit(
                embed=discord.Embed(
                    title="Something went wrong!",
                    description="this issue is already sent to Rei",
                    color=Color.failed,
                )
            )

        embed.set_footer(text="Successfully edited")
        embed.title = "Member lineup info changed"
        embed.color = Color.success
        await msg.edit(embed=embed, view=None)

    @app_commands.command()
    async def info(
        self, interaction: Interaction, member: Optional[discord.Member] = None
    ):
        """
        View a member lineup info

            Parameters
            -----------
            member:
                the member to view information, if ommitted this points to yourself
        """
        member = member or interaction.user
        await interaction.response.defer()

        result = await self.bot.db.select(f"players:{member.id}")
        if result is None:
            keyword = (
                "This person is" if member.id != interaction.user.id else "You are"
            )
            return await interaction.followup.send(f"{keyword} not in the lineup")

        user = await self.get_user_by_id(result["rblx_id"])
        if user is not None:
            avatar = await self.get_avatar_from_id(user["id"])

        embed = discord.Embed(title="Member lineup info", color=discord.Color.random())
        if user:
            embed.set_thumbnail(url=avatar)
            embed.add_field(
                name="Roblox username",
                value="{0} (@{1})".format(user["displayName"], user["name"]),
            )
        else:
            embed.description = "*⚠️ Failed to find this member's Roblox ⚠️*"
        embed.add_field(
            name="Positions",
            value="{0}\n*Playing position: {1}*".format(
                format_roles(positions_to_roles(result["positions"])),
                f"<@&{roles[result['playing_position']]}>",
            ),
        )
        embed.add_field(name="Roster", value=result["roster"].capitalize())
        embed.add_field(name="Jersey number", value=result["jersey"] or "N/A")

        await interaction.followup.send(embed=embed)


async def setup(bot: Bot):
    await bot.add_cog(Lineup(bot))
