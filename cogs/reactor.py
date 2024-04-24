import os
from typing import Final

import discord
from discord import Intents, Client, Message, Interaction, Reaction, app_commands
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
        # self.active: bool = False
        self.channel: discord.interactions.InteractionChannel = None
        self.emojis: list[str] = []
        self.history: dict = {"msgs": [], "emojis": []}

    # SLASH COMMAND: REMOVES MOST RECENT REACTIONS
    @app_commands.command()
    async def react_undo(self, inter: Interaction) -> None:
        """Removes the most recently applied emojis

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        """
        if not self.history["msgs"] or not self.history["emojis"]:
            await inter.response.send_message(
                "No reactions to remove...", ephemeral=True
            )
            return

        await inter.response.send_message(
            "Removing latest reactions...", ephemeral=True
        )
        for i, msg in enumerate(self.history["msgs"]):
            for emoji in self.history["emojis"][i]:
                await msg.remove_reaction(emoji, self.bot.user)

        await inter.edit_original_response(content="Removed latest reactions!")

    # SLASH COMMAND: REMOVES ALL BOT REACTIONS
    @app_commands.command()
    async def react_remove(
        self, inter: Interaction, number_of_messages: int = 10
    ) -> None:
        """Removes all of the bot's recent reactions in the current channel or thread (default: 10 messages)

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        number_of_messages: int = 10 (optional)
            How many messages to search through for Rap's Reactor reactions (max: 100)
        """
        await inter.response.send_message(
            f"Removing reactions from the {min(number_of_messages, 100)} most recent messages...",
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
    async def react_now(self, inter: Interaction, emojis: str = None) -> None:
        """Reacts to every message in this channel or thread with the given emojis until /react is used again with no arguments

        Reacts with the given emojis to all messages in the current channel or thread until the command is called again or timeouts. Calling /react again updates the emojis used to react.

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        emojis : str, optional
            The emojis to react with, if empty the bot is toggled off
        """
        if emojis:
            self.channel = inter.channel
            emoji_list, msg = await self.__extract_emoji(inter, emojis)
            if emoji_list:
                self.history: dict = {"msgs": [], "emojis": []}
                self.emojis = emoji_list
                await inter.response.send_message(
                    f"Reacting with {' '.join(self.emojis)} {' '.join(msg)}",
                    ephemeral=True,
                )
            else:
                self.channel = None
                await inter.response.send_message(
                    f"You must provide at least one valid emoji", ephemeral=True
                )
        else:
            self.channel = None
            await inter.response.send_message(
                f"Auto reacting has ended!", ephemeral=True
            )

    # SLASH COMMAND: REACT TO THREAD
    @app_commands.command()
    async def react_past(
        self, inter: Interaction, emojis: str, number_of_messages: int = 32
    ) -> None:
        """Reacts to every message in this channel between your own reactions of :arrow_up: :arrow_down:

        Parameters
        ----------
        inter : Interaction
            Interaction object given by the Discord API
        emojis : str
            The emojis to react with, if empty the bot is toggled off
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
                            self.history = {
                                "msgs": msgs,
                                "emojis": [self.emojis] * len(msgs),
                            }
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

    # LISTENER: ON MESSAGE REACT TO MESSAGE
    @commands.Cog.listener("on_message")
    async def react_now_reactor(self, msg: Message) -> None:
        """Reacts to every message in this channel or thread until /react is used again with no arguments

        Reacts with the given emojis to all messages in the current channel or thread until the command is called again or timeouts. Calling /react again updates the emojis used to react

        Parameters
        ----------
        msg : Message
            The Message object given by the Discord API
        """
        if (
            msg.author.bot
            or not self.channel
            or not self.emojis
            or msg.channel.id != self.channel.id
        ):
            return

        for emoji in self.emojis:
            print(f"Reacting with {emoji} in {msg.guild}.{msg.channel} : {msg.author}")
            await msg.add_reaction(f"{emoji}")

        self.history["msgs"].append(msg)
        self.history["emojis"].append(self.emojis)

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
