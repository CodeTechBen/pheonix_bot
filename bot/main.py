"""Main file for Discord bot"""
# pylint: disable=redefined-outer-name

from os import environ as ENV
from dotenv import load_dotenv
from psycopg2.extensions import connection
import discord
from discord.ext import commands
from db_function import get_connection, upload_server, generate_class
from validation import is_valid_class

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

    @bot.command()
    async def create_class(ctx, class_name: str = None, is_playable: bool = None):
        """Creates a class in the database"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return
        
        if class_name is None or is_playable is None or not is_valid_class(class_name, is_playable):
            await ctx.send("Usage: !create_class <class_name> <True/False>")
            return
        
        response = generate_class(ctx.guild, class_name, is_playable, conn)
        await ctx.send(response)

if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
