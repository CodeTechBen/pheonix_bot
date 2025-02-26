"""Main file for Discord bot"""
# pylint: disable=redefined-outer-name

from os import environ as ENV
from dotenv import load_dotenv
from psycopg2.extensions import connection
import discord
from discord.ext import commands
from db_function import (get_connection,
                         upload_server,
                         generate_class,
                         generate_race,
                         get_player_mapping,
                         create_player,
                         get_location_mapping,
                         generate_location,
                         get_settlement_mapping,
                         generate_settlement)
from validation import (is_valid_class,
                        is_valid_settlement)

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

        if not is_valid_class(class_name, is_playable):
            await ctx.send("Usage: !create_class <class_name> <True/False>")
            return

        response = generate_class(ctx.guild, class_name.title(), is_playable, conn)
        await ctx.send(response)


    @bot.command()
    async def create_race(ctx, race_name: str = None, is_playable: bool = None, speed: int = 30):
        """Creates a race in the database"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return

        if not is_valid_class(race_name, is_playable):
            await ctx.send("Usage: !create_race <class_name> <True/False> <speed?>")
            return

        if not isinstance(speed, int):
            return

        response = generate_race(ctx.guild, race_name.title(), is_playable, speed, conn)
        await ctx.send(response)

    @bot.command()
    async def create_character(ctx,
                               character_name: str = None,
                               race_name: str = None,
                               class_name: str = None):
        """Creates a player character in the database"""
        player_map = get_player_mapping(conn, ctx.guild.id)
        player_name = ctx.author.name
        if player_name in player_map.keys():
            player_id = player_map.get(player_name)
        else:
            player_id = create_player(ctx, conn)

    @bot.command()
    async def create_settlement(ctx):
        """Sets a channel as a location"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return
        is_valid, message = is_valid_settlement(ctx)
        if not is_valid:
            await ctx.send(message)
            return

        await ctx.send(
            f"Forum Channel: **{ctx.channel.parent.name}** (ID: `{ctx.channel.parent.id}`)\n"
            f"Thread: **{ctx.channel.name}** (ID: `{ctx.channel.id}`)"
        )

        location_map = get_location_mapping(conn, ctx.guild.id)
        if ctx.channel.parent.id not in location_map.keys():
            print(
                f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.parent.id}")
            await ctx.send(generate_location(ctx, conn))
            print(f"Generated Location {ctx.channel.parent.name}")

        settlement_map = get_settlement_mapping(conn, ctx.guild.id)
        if ctx.channel.id not in settlement_map.keys():
            await ctx.send(generate_settlement(ctx, conn, location_map))


if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
