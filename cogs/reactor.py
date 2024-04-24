import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Bot

import emoji as emji
import re


class Reactor(commands.Cog):
    """A class which provides the /react command and its supporting functionality

    Parameters
    ----------
    bot : Bot
        The top level discord.ext.commands.Bot object used for API interactions
    active : bool
        The current state of the reaction bot
    """

    def __init__(self, bot: Bot) -> None:
        """
        Parameters
        ----------
        bot : Bot
            The top level discord.ext.commands.Bot object used for API interactions
        """
        self.bot: Bot = bot
        self.emojis: list[str] = []

    # SLASH COMMAND: REMOVES ALL BOT REACTIONS
    @app_commands.command()
    async def remove(self, inter: Interaction, number_of_messages: int = 10) -> None:
        """Removes all recent Rap's Reactor reactions in the current channel or thread (max: 100 messages, default: 10 messages)

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        number_of_messages: int = 10 (optional)
            How many messages to search through for this bot's reactions (max: 100)
        """
        await inter.response.send_message(
            f"Removing this bot's reactions from the {min(number_of_messages, 100)} most recent messages...",
            ephemeral=True,
        )

        async for msg in inter.channel.history(limit=min(number_of_messages, 100)):
            for reaction in msg.reactions:
                async for user in reaction.users():
                    if user == self.bot.user:
                        await reaction.remove(user)

        await inter.edit_original_response(
            content=f"Removed reactions from the {min(number_of_messages, 100)} most recent messages!"
        )

    # SLASH COMMAND: REACT TO THREAD
    @app_commands.command()
    async def react(
        self, inter: Interaction, emojis: str, number_of_messages: int = 32
    ) -> None:
        """Reacts to every message in this channel between your own reactions of :arrow_up: and :arrow_down: (pointing inwards)

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        emojis : str
            The emojis to react with
        number_of_messages : int (optional)
            How many recent messages to search through (default: 32, max: 100)
        """
        if emojis:
            emoji_list, msg = await self.__extract_emoji(inter, emojis)
            if emoji_list:
                self.emojis = emoji_list
                await inter.response.send_message(
                    f"Reacting with {' '.join(self.emojis)} {' '.join(msg)}",
                    ephemeral=True,
                )

                msgs: list[Interaction.message] = []
                async for msg in inter.channel.history(
                    limit=min(number_of_messages, 100)
                ):
                    if msgs:
                        msgs.append(msg)

                    reactions = [str(x) for x in msg.reactions]
                    if "⬆️" in reactions:
                        msgs.append(msg)
                    if "⬇️" in reactions:
                        if msgs:
                            for msg in msgs:
                                for emoji in self.emojis:
                                    print(
                                        f"Reacting with {emoji} in {msg.guild}.{msg.channel} : {msg.author}"
                                    )
                                    await msg.add_reaction(f"{emoji}")
                            return
                await inter.edit_original_response(
                    content=f"Bounds not found. Please ensure at least one message is bounded by ⬆️ and ⬇️ reactions (pointing inwards)."
                )
            else:
                await inter.response.send_message(
                    f"You must provide at least one valid emoji", ephemeral=True
                )
        else:
            await inter.response.send_message(
                f"You must provide at least one valid emoji", ephemeral=True
            )

    async def __extract_emoji(self, inter: Interaction, emojis: str) -> list[str]:
        """Breaks a string emojis and custom emoji ids

        Parameters
        ----------
        emoji_str : str
            The string with both text and emojis

        Returns
        -------
        output : List[str]
            The extracted unicode emojis and Discord custom emojis in the form of <:{name}:{id}>
        """
        output: list[str] = []
        msg: list[str] = []

        emoji_split: list[str] = []
        emoji_dict: list[any] = emji.emoji_list(emojis)
        prev = {"match_start": 0, "match_end": -1, "emoji": ""}

        for emoji in emoji_dict:
            emoji_split.append(emojis[prev["match_end"] + 1 : emoji["match_start"]])
            emoji_split.append(emoji["emoji"])
            prev = emoji
        emoji_split.append(emojis[prev["match_end"] + 1 :])

        emoji_split = [
            x.strip() for x in emoji_split if x.strip()
        ]  # Removes strings with just white space and removes excess white space

        for emoji in emoji_split:
            if emji.is_emoji(emoji):
                output.append(emoji)
            elif c := re.findall(
                "<:.{1,32}:[0-9]{0,20}>", emoji
            ):  # regex for Discord custom emojis in the form of <:{name}:{id}>
                for regx in c:
                    try:
                        emoji_exists = await inter.guild.fetch_emoji(
                            regx.split(":")[-1][:-1]
                        )
                        output.append(str(emoji_exists))
                    except (discord.errors.NotFound, discord.errors.HTTPException) as e:
                        msg.append(f"\t[*MISSING -> {regx}*]")
            else:
                continue

        output = list(dict.fromkeys(output).keys())  # Keep only distinct strings

        return output, msg
