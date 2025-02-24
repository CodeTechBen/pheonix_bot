"""Main file for Discord bot"""
# pylint: disable=redefined-outer-name

from os import environ as ENV
from dotenv import load_dotenv
from psycopg2.extensions import connection
import discord
from discord.ext import commands
from db_function import get_connection, upload_server

def create_bot() -> commands.Bot:
    """Initializes and returns the bot"""

    intents = discord.Intents.default()
    intents.message_content = True  # Required for message-based commands

    bot = commands.Bot(command_prefix="!", intents=intents)

    conn = get_connection()
    register_events(bot, conn)
    register_commands(bot, conn)

    return bot


def register_events(bot: commands.Bot, conn: connection):
    """Registers event handlers for the bot"""

    @bot.event
    async def on_ready():
        """When turned on prints message"""
        print(f'Logged in as {bot.user}')


    @bot.event
    async def on_guild_join(ctx):
        """Triggered when the bot joins a new server"""
        await ctx.send(upload_server(ctx.guild, conn))


def register_commands(bot: commands.Bot, conn: connection):
    """Registers command functions"""

    @bot.command()
    async def add_server(ctx):
        """Manually uploads the server to the DB"""
        await ctx.send(upload_server(ctx.guild, conn))

if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
