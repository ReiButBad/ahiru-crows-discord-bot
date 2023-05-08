import discord
import traceback
from typing import Union
from discord.ext import commands
from discord import app_commands
from discord.interactions import Interaction
from discord.ui.item import Item
from lib.constants import (
    roles,
    positions,
    strings,
    target_guild_id,
    tryout_score_channel_id,
)
from lib.utils import format_roles, is_helper, positions_to_roles


class ScoreView(discord.ui.View):
    def __init__(self, user: Union[discord.User, discord.Member], embed: discord.Embed):
        self.user = user
        self.positions: list[str] = []
        self.embed = embed
        super().__init__()

    async def interaction_check(self, interaction: Interaction):
        if self.user.id == interaction.user.id:
            return True

        await interaction.response.send_message(
            "This is not your interaction", ephemeral=True
        )
        return False

    async def on_error(self, interaction: Interaction, error: Exception, item: Item):
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
            self.positions.remove(select.values[0])

        self.embed.description = "Positions: {0}".format(
            format_roles(positions_to_roles(self.positions))
        )
        await interaction.response.edit_message(view=self, embed=self.embed)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.gray)
    async def button_done(self, interaction: Interaction, btn: discord.ui.Button):
        self.stop()

        self.button_done.disabled = True
        self.select_positions.disabled = True


class ModalComments(discord.ui.Modal, title="Tryout comment"):
    comment = discord.ui.TextInput(
        label="Comment (leave blank for no comment)",
        style=discord.TextStyle.paragraph,
        placeholder="fast reaction time, nice dives, missed some of the spikes, consistent serves, etc....",
        required=False,
    )

    async def on_submit(self, interaction: Interaction):
        await interaction.response.edit_message(
            content="Success!", embed=None, view=None
        )


class ModalInvoker(discord.ui.View):
    def __init__(self, user: discord.User, target: discord.Member):
        self.target = target
        self.comment = ""
        self.user = user
        super().__init__()

    async def interaction_check(self, interaction: Interaction):
        if self.user.id == interaction.user.id:
            return True

        await interaction.response.send_message(
            "This is not your interaction", ephemeral=True
        )
        return False

    @discord.ui.button(label="Tryout comment", style=discord.ButtonStyle.primary)
    async def add_comment(self, interaction: Interaction, _btn):
        modal = ModalComments()
        await interaction.response.send_modal(modal)
        await modal.wait()
        self.comment = modal.comment.value
        self.stop()


class Tryout(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.guild_only
    @app_commands.check(is_helper)
    @app_commands.guilds(target_guild_id)
    async def score(
        self,
        interaction: Interaction,
        member: discord.Member,
        string: app_commands.Range[int, 1, 3],
        serves: app_commands.Range[float, 0, 10],
        receives: app_commands.Range[float, 0, 30],
        sets: app_commands.Range[float, 0, 10],
        spikes: app_commands.Range[float, 0, 10],
        blocks: app_commands.Range[float, 0, 10],
    ):
        """
        Process a user's score and share it to tryout-score

            Parameters
            -----------
            member:
                the member to score

            string:
                the string this user will be in

            serves:
                the service score (ranges from 0-10 and can be decimal value)

            receives:
                the receive score (ranges from 0-30 and can be decimal value)

            sets:
                the setting score (ranges from 0-10 and can be decimal value)

            spikes:
                the spiking score (ranges from 0-10 and can be decimal value)

            blocks:
                the blocking score (ranges from 0-10 and can be decimal value)
        """
        await interaction.response.defer()
        embed = discord.Embed(
            title="Pick user's positions (can be more than 1)",
            color=discord.Color.random(),
            description="Positions: ",
        )
        embed.set_author(icon_url=member.display_avatar.url, name=member.display_name)
        scores = {
            "Serves": f"{serves}/10",
            "Receives": f"{receives}/30",
            "Sets": f"{sets}/10",
            "Spikes": f"{spikes}/10",
            "Blocks": f"{blocks}/10",
            "Total": f"{serves+receives+sets+spikes+blocks}/70",
        }
        embed.add_field(
            name="Scores",
            value="{0}\n\n".format(
                "\n".join([f"{i[0]}: {i[1]}" for i in scores.items()])
            ),
            inline=False,
        )
        embed.add_field(
            name="Guide",
            value="1. Pressing done without any positions selected will cancel the scoring process\n2. Selecting the same positions will remove it from the selection",
            inline=False,
        )

        view = ScoreView(interaction.user, embed)
        view.msg = await interaction.followup.send(
            "Select user positions", view=view, embed=embed, wait=True
        )
        timed_out = await view.wait()
        if timed_out:
            return
        if len(view.positions) == 0:
            return await view.msg.edit(content="Cancelled", embed=None, view=None)
        modal_view = ModalInvoker(interaction.user, member)
        await view.msg.edit(content="", embed=None, view=modal_view)
        await modal_view.wait()
        embed = discord.Embed(
            title=f"{member} tryout result",
            color=self.bot.get_guild(target_guild_id).get_role(strings[string]).color,
        )
        embed.add_field(
            name="Score",
            value="{0}\n\n".format(
                "\n".join([f"{i[0]}: *{i[1]}*" for i in scores.items()])
            ),
            inline=False,
        )
        embed.add_field(
            name="Positions",
            value=", ".join([f"<@&{roles[i]}>" for i in view.positions]),
            inline=False,
        )
        if len(modal_view.comment) > 0:
            embed.add_field(name="Comments", value=modal_view.comment)
        try:
            await member.add_roles(*[discord.Object(i) for i in view.positions])
        except discord.HTTPException:
            embed.set_footer(text="Error: roles cannot be added automatically")
        await self.bot.get_channel(tryout_score_channel_id).send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tryout(bot))
