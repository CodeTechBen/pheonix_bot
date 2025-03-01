"""Main file for Discord bot"""
# pylint: disable=redefined-outer-name

from os import environ as ENV
from random import randint
from datetime import datetime, timedelta
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
                         generate_settlement,
                         get_character_mapping,
                         get_race_map,
                         get_class_map,
                         get_spell_type_map,
                         generate_character,
                         generate_spell,
                         get_element_map,
                         get_spell_status_map,
                         generate_events_for_character,
                         generate_inventory_for_character)

from player_functions import (get_potential_player_spells,
                              add_spell_to_character,
                              get_equipped_spells,
                              increase_wallet,
                              update_last_event,
                              get_last_event,
                              create_item)

from validation import (is_valid_class,
                        is_valid_settlement)

from utils import (create_embed,
                   get_input,
                   get_player_id,
                   get_character_id,
                   get_inventory_id,
                   get_items_in_inventory,
                   create_inventory_embed)

def create_bot() -> commands.Bot:
    """Initializes and returns the bot"""

    intents = discord.Intents.default()
    intents.message_content = True  # Required for message-based commands

    bot = commands.Bot(command_prefix="!", intents=intents)

    conn = get_connection()
    register_events(bot, conn)

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

if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
