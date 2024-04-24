import os
from typing import Final

import discord
from discord import Intents, Client, Message, Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Bot


class Debug(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # SLASH COMMAND: PING
    @app_commands.command(name="ping", description="Replies with 'pong'")
    @commands.is_owner()
    async def ping(self, inter: Interaction) -> None:
        await inter.response.send_message("pong", ephemeral=True)


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    # SYNC COMMAND TREE
    @app_commands.command(
        name="sync_commands", description="Updates the bot's command tree"
    )
    @commands.is_owner()
    async def sync_commands(self, inter: Interaction) -> None:
        if inter.user.id == 142080839214301184:
            await inter.response.send_message("Syncing...", ephemeral=True)
            try:
                await self.bot.tree.sync()
                await inter.edit_original_response(content="Success!")
                # await inter.followup.send('Success!', ephemeral=True)
            except Exception as e:
                await inter.edit_original_response(content="Failed to sync commands")
                # await inter.followup.send('Failed to sync commands', ephemeral=True)
                raise (f"Failed to sync command tree {e}")
        else:
            await inter.response.send_message(
                "You don't have permission for this command", ephemeral=True
            )
