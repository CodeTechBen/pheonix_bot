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
            generate_events_for_character(conn, ctx.author.name)
            generate_inventory_for_character(conn, ctx.author.name)
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

    @bot.command()
    async def add_spell(ctx):
        """Allows a player to assign a spell to their selected character"""
        player_spells = get_potential_player_spells(conn, ctx)
        if not player_spells:
            await ctx.send("You have no spells available to learn.")
            return

        spell_id_list = []

        # Create an embed for each spell
        for spell in player_spells:
            spell_id = spell["spell_id"]
            spell_name = spell["spell_name"]
            spell_desc = spell["spell_description"]
            spell_power = spell["spell_power"]
            mana_cost = spell["mana_cost"]
            cooldown = spell["cooldown"]
            element_name = spell["element_name"]
            status_name = spell["status_name"]
            chance = spell["chance"]
            duration = spell["duration"]

            spell_id_list.append(spell_id)  # Store valid spell IDs

            embed = discord.Embed(
                title=f"Spell: {spell_name}", color=discord.Color.blue())
            embed.add_field(name="Description", value=spell_desc, inline=False)
            embed.add_field(name="Power", value=str(spell_power))
            embed.add_field(name="Mana Cost", value=str(mana_cost))
            embed.add_field(name="Cooldown", value=f"{cooldown} turns")
            embed.add_field(name="Element", value=element_name)

            # Add status effects if they exist
            if status_name:
                embed.add_field(
                    name="Status Effect", value=f"{status_name} ({chance}% for {duration} turns)", inline=False)

            embed.set_footer(text=f"Spell ID: {spell_id}")

            await ctx.send(embed=embed)

        # Ask for the player's input
        await ctx.send("Reply with the Spell ID of the spell you want to learn.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await bot.wait_for("message", timeout=30.0, check=check)
            selected_spell_id = int(msg.content)

            if selected_spell_id not in spell_id_list:
                await ctx.send("Invalid Spell ID. Please try again.")
                return

            add_spell_to_character(conn, ctx, selected_spell_id)

            await ctx.send(f"Spell {selected_spell_id} has been added to your character!")

        except TimeoutError:
            await ctx.send("⏳ You took too long to respond. Try again.")

    @bot.command()
    async def spellbook(ctx):
        """Checks the equipped spells"""
        equipped_spells = get_equipped_spells(conn, ctx)
        if not equipped_spells:
            await ctx.send("You have no spells equipped.")
            return
        for spell in equipped_spells:
            embed = discord.Embed(
                title=f"Spell {spell.get('spell_name')}",
                description=spell.get('spell_description'),
                color=discord.Color.blue()
            )
            embed.add_field(name="Mana Cost", value=spell.get('mana_cost'))
            embed.add_field(name="Cooldown", value=f"{spell.get('cooldown')} turns")
            embed.add_field(name="Element", value=spell.get('element_name'))

            if spell.get('status_name'):
                embed.add_field(
                    name="Status Effect",
                    value=f"{spell.get('status_name')} ({spell.get('chance')}% for {spell.get('duration')} turns)", inline=False)

            embed.set_footer(text=f"Spell ID: {spell.get('spell_id')}")
            await ctx.send(embed=embed)

    @bot.command()
    async def scavenge(ctx):
        """allows the player to scavenge for money"""
        last_scavenged = get_last_event(conn, ctx.author.name, 'Scavenge')

        if last_scavenged:
            now = datetime.now()
            # Convert to minutes
            time_since_last = (now - last_scavenged).total_seconds() / 60

            max_shards = 120
            min_shards = time_since_last/2

            if time_since_last < 1:
                await ctx.send(f"Sorry {ctx.author.display_name}, you can't scavenge so soon! Wait at least 1 minute.")
                return

            # Random shards based on time waited
            profit = randint(
                int(round(min(max_shards/2, min_shards))),
                int(round(min(int(time_since_last), max_shards)))
            )
            message = increase_wallet(conn, ctx.author.name, profit)
            update_last_event(conn, ctx.author.name, 'Scavenge', now)

            await ctx.send(message)
        else:
            await ctx.send(f"{ctx.author.display_name}, you need to create a character first!")


    @bot.command()
    async def craft(ctx, item_name: str, item_value: int):
        """Lets a player craft an item"""
        # Get the last crafted time for the player
        last_crafted = get_last_event(conn, ctx.author.name, 'Craft')

        if last_crafted:
            # Calculate the time difference from the last crafted event
            time_since_last = datetime.now() - last_crafted

            # If the player crafted in the last 3 hours, block the crafting
            if time_since_last < timedelta(hours=3):
                await ctx.send(f"You can't craft right now. Please wait {3 - time_since_last.seconds // 3600} hour(s) before crafting again.")
                return

        # If the player hasn't crafted recently, proceed with creating the item
        message = create_item(conn, ctx.author.name, item_name, item_value)
        await ctx.send(message)


    @bot.command()
    async def inventory(ctx, inventory_name: str = None):
        """Shows the player their inventory in an embed"""

        # Get player_id using player_name and server_id
        player_id = get_player_id(conn, ctx.author.name, ctx.guild.id)
        if not player_id:
            await ctx.send("Player not found!")
            return

        # Get character_id for the player
        character_id = get_character_id(conn, player_id)
        if not character_id:
            await ctx.send("No character selected for this player.")
            return

        # Get inventory_id for the character
        inventory_id = get_inventory_id(conn, character_id)
        if not inventory_id:
            await ctx.send("This character does not have an inventory.")
            return

        # Get items in the inventory
        items = get_items_in_inventory(conn, inventory_id)
        if not items:
            await ctx.send("Your inventory is empty.")
            return

        # Create the embed and send it
        embed = create_inventory_embed(ctx, items)
        await ctx.send(embed=embed)


if __name__ == "__main__":
    load_dotenv()
    bot = create_bot()
    bot.run(ENV['DISCORD_TOKEN'])
