"""Main file for Discord bot"""
# pylint: disable=redefined-outer-name

from os import environ as ENV
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
import discord
from discord.ext import commands

# Load environment variables
load_dotenv()

# Database connection pool
def get_connection() -> connection:
    """Returns a postgres connection"""
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname=ENV['DB_NAME'],
        user=ENV['DB_USER'],
        host=ENV['DB_HOST'],
        port=ENV['DB_PORT'],
        cursor_factory=RealDictCursor)
    print("Connected to database.")
    return conn

def create_bot() -> commands.Bot:
    """Initializes and returns the bot"""

    intents = discord.Intents.default()
    intents.message_content = True  # Required for message-based commands

    bot = commands.Bot(command_prefix="!", intents=intents)

    # Register event handlers & commands separately
    register_events(bot)
    register_commands(bot)

    return bot


def register_events(bot: commands.Bot):
    """Registers event handlers for the bot"""

    async def on_ready():
        print(f"Logged in as {bot.user}")

    bot.event(on_ready)


def register_commands(bot: commands.Bot):
    """Registers command functions"""

    async def scavenge(ctx):
        """lets the user scavenge for shards"""
        await ctx.send("Pong!")

    bot.command()(scavenge)


if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
