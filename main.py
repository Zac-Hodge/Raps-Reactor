# OS + OTHER
import os
from typing import Final
from dotenv import load_dotenv

# DISCORD
import discord
from discord import Intents, Client, Message, Interaction, app_commands
from discord.ext import commands
from discord.ext.commands import Bot

# RAP'S REACTOR'S COGS
from cogs.reactor import Reactor
from cogs.owner import Debug, Admin


# LOAD API TOKEN
load_dotenv()
TOKEN: Final[str] = os.getenv("DISCORD_TOKEN")

# BOT SETUP
intents: Intents = Intents.none()
intents.guild_messages = True
intents.guild_reactions = True
bot: Bot = Bot(command_prefix="/", intents=intents)


# BOT STARTUP
@bot.event
async def on_ready() -> None:
    print(f"{bot.user} is connected!")

    # Add cogs
    try:
        await bot.add_cog(Reactor(bot))
        await bot.add_cog(Debug(bot))
        await bot.add_cog(Admin(bot))

    except Exception as e:
        raise (f"Failed to add cog(s) {e}")

    # Sync command tree
    try:
        await bot.tree.sync()
    except Exception as e:
        raise (f"Failed to sync command tree {e}")


# START BOT
def main() -> None:
    bot.run(token=TOKEN)


if __name__ == "__main__":
    main()
