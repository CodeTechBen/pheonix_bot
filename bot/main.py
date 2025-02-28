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
                         generate_settlement,
                         get_character_mapping,
                         get_race_map,
                         get_class_map,
                         get_spell_type_map,
                         generate_character,
                         generate_spell,
                         get_element_map,
                         get_spell_status_map)
from validation import (is_valid_class,
                        is_valid_settlement)
from utils import (create_embed,
                   get_input)

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

        character_map = get_character_mapping(conn, player_id)
        if character_name in character_map.keys():
            await ctx.send(f'{character_name} already exists, please choose a new name.')
            return

        race_map = get_race_map(conn, ctx.guild.id)
        class_map = get_class_map(conn, ctx.guild.id)
        race_id = race_map.get(race_name, None)
        class_id = class_map.get(class_name, None)
        if character_name and race_id and class_id:
            response = generate_character(conn, ctx, character_name, race_id, class_id, player_id)
            await ctx.send(response)
        else:
            await ctx.send("Invalid character name, race or class. ")


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
        location_map = get_location_mapping(conn, ctx.guild.id)
        settlement_map = get_settlement_mapping(conn, ctx.guild.id)
        if ctx.channel.id not in settlement_map.keys():
            await ctx.send(generate_settlement(ctx, conn, location_map))

    @bot.command()
    async def create_spell(ctx):
        """Command to generate a spell"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send('You must be an admin to use this command.')
            return

        spell_name = await get_input(ctx, bot, "📝 Enter the spell name:")
        if not spell_name:
            return

        spell_description = await get_input(ctx, bot, "📖 Enter spell description:")
        if not spell_description:
            return

        spell_power = await get_input(ctx, bot, "💥 Enter spell power (1-100):", int)
        if spell_power is None:
            return

        mana_cost = await get_input(ctx, bot, "🔋 Enter mana cost:", int)
        if mana_cost is None:
            return

        cooldown = await get_input(ctx, bot, "⏳ Enter cooldown (in turns):", int, True)
        if cooldown is None:
            return

        scaling_factor = await get_input(ctx, bot, "🎚️ Enter scaling factor (0.1 - 2.0):", float)
        if scaling_factor is None:
            return

        # Fetch spell types
        spell_types = get_spell_type_map(conn)
        if not spell_types:
            await ctx.send("❌ No spell types found in the database.")
            return

        await ctx.send(embed=create_embed(
            "📜 Spell Types", "Available spell types:", spell_types, discord.Color.blue()))
        spell_type_id = await get_input(ctx, bot, "⚡ Enter the **ID** of the spell type:", int)
        if spell_type_id is None or spell_type_id not in spell_types:
            await ctx.send("❌ Invalid spell type ID. Try again.")
            return

        # Fetch Elements
        element_map = get_element_map(conn)
        await ctx.send(embed=create_embed(
            "🔥 Elements", "Available Elements", element_map, discord.Color.red()))
        element_id = await get_input(ctx, bot, "🔥 Enter the **ID** of the element:", int)

        # Fetch available classes
        classes = get_class_map(conn, ctx.guild.id)
        await ctx.send(embed=create_embed(
            "🛡️ Classes", "Available classes:", classes, discord.Color.green()))
        class_id = await get_input(
            ctx, bot, "⚔️ Enter the **ID** of the class (or `0` if none):", int, True)
        class_id = None if class_id == 0 else class_id

        # Fetch available races
        races = get_race_map(conn, ctx.guild.id)
        await ctx.send(embed=create_embed(
            "🧬 Races", "Available races:", races, discord.Color.purple()))
        race_id = await get_input(
            ctx, bot, "🧬 Enter the **ID** of the race (or `0` if none):", int, True)
        race_id = None if race_id == 0 else race_id

        # Fetch spell statuses
        spell_statuses = get_spell_status_map(conn)
        await ctx.send(embed=create_embed("🌀 Spell Status Effects",
                                        "Available status effects:",
                                        spell_statuses,
                                        discord.Color.purple()))
        spell_status_id = await get_input(
            ctx, bot, "🌀 Enter the **ID** of the spell status effect:", int, True)
        spell_status_chance = await get_input(ctx, bot, r"% chance of status condition!", int)
        spell_duration = await get_input(ctx, bot, "Duration of status condition (in turns)", int)

        # Generate the spell
        response = generate_spell(
            conn, ctx.guild.id, spell_name, spell_description, spell_power,
            mana_cost, cooldown, scaling_factor, spell_type_id, element_id,
            spell_status_id, spell_status_chance, spell_duration, class_id, race_id
        )
        await ctx.send(response)



if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
