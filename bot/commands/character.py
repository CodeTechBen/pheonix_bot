"""Defines the Character commands

- !add_spell: adds a spell to the character to use in battle from a list of spells
- !spellbook: lets the player see the spells they have equipped
- !scavenge: lets the player get money from scavenging
- !craft: lets the player create a item that they can sell or enchant
- !inventory: lets the player view their inventory
"""
from random import randint
import discord
from discord.ext import commands
from psycopg2.extensions import connection

class Character(commands.Cog):
    """Commands for managing player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn

    @commands.command()
    async def create_character(self, ctx, character_name: str = None, race_name: str = None, class_name: str = None):
        """Creates a player character in the database"""
        player_map = get_player_mapping(self.conn, ctx.guild.id)
        player_name = ctx.author.name
        if player_name in player_map.keys():
            player_id = player_map.get(player_name)
        else:
            player_id = create_player(ctx, self.conn)

        character_map = get_character_mapping(self.conn, player_id)
        if character_name in character_map.keys():
            await ctx.send(f'{character_name} already exists, please choose a new name.')
            return

        race_map = get_race_map(self.conn, ctx.guild.id)
        class_map = get_class_map(self.conn, ctx.guild.id)
        race_id = race_map.get(race_name, None)
        class_id = class_map.get(class_name, None)
        if character_name and race_id and class_id:
            response = generate_character(
                self.conn, ctx, character_name, race_id, class_id, player_id)
            generate_events_for_character(self.conn, ctx.author.name)
            generate_inventory_for_character(self.conn, ctx.author.name)
            await ctx.send(response)
        else:
            await ctx.send("Invalid character name, race or class. ")
    
    @commands.command()
    async def add_spell(self, ctx):
        """Allows a player to assign a spell to their selected character"""
        player_spells = get_potential_player_spells(self.conn, ctx)
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

            add_spell_to_character(self.conn, ctx, selected_spell_id)

            await ctx.send(f"Spell {selected_spell_id} has been added to your character!")

        except TimeoutError:
            await ctx.send("⏳ You took too long to respond. Try again.")
    
    @commands.command()
    async def spellbook(ctx):
        """Checks the equipped spells"""
        equipped_spells = get_equipped_spells(self.conn, ctx)
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
            embed.add_field(name="Cooldown",
                            value=f"{spell.get('cooldown')} turns")
            embed.add_field(name="Element", value=spell.get('element_name'))

            if spell.get('status_name'):
                embed.add_field(
                    name="Status Effect",
                    value=f"{spell.get('status_name')} ({spell.get('chance')}% for {spell.get('duration')} turns)", inline=False)

            embed.set_footer(text=f"Spell ID: {spell.get('spell_id')}")
            await ctx.send(embed=embed)


    @bot.command()
    async def scavenge(self, ctx):
        """allows the player to scavenge for money"""
        last_scavenged = get_last_event(self.conn, ctx.author.name, 'Scavenge')

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
            message = increase_wallet(self.conn, ctx.author.name, profit)
            update_last_event(self.conn, ctx.author.name, 'Scavenge', now)

            await ctx.send(message)
        else:
            await ctx.send(f"{ctx.author.display_name}, you need to create a character first!")

    @commands.command()
    async def craft(self, ctx, item_name: str, item_value: int):
        """Lets a player craft an item"""
        # Get the last crafted time for the player
        last_crafted = get_last_event(self.conn, ctx.author.name, 'Craft')

        if last_crafted:
            # Calculate the time difference from the last crafted event
            time_since_last = datetime.now() - last_crafted

            # If the player crafted in the last 3 hours, block the crafting
            if time_since_last < timedelta(hours=3):
                await ctx.send(f"You can't craft right now. Please wait {3 - time_since_last.seconds // 3600} hour(s) before crafting again.")
                return

        # If the player hasn't crafted recently, proceed with creating the item
        message = self.create_item(self.conn, ctx.author.name, item_name, item_value)
        await ctx.send(message)

    @commands.command()
    async def inventory(self, ctx):
        """Shows the player their inventory in an embed"""

        # Get player_id using player_name and server_id
        player_id = get_player_id(self.conn, ctx.author.name, ctx.guild.id)
        if not player_id:
            await ctx.send("Player not found!")
            return

        # Get character_id for the player
        character_id = get_character_id(self.conn, player_id)
        if not character_id:
            await ctx.send("No character selected for this player.")
            return

        # Get inventory_id for the character
        inventory_id = get_inventory_id(self.conn, character_id)
        if not inventory_id:
            await ctx.send("This character does not have an inventory.")
            return

        # Get items in the inventory
        items = get_items_in_inventory(self.conn, inventory_id)
        if not items:
            await ctx.send("Your inventory is empty.")
            return

        # Create the embed and send it
        embed = create_inventory_embed(ctx, items)
        await ctx.send(embed=embed)
    

    def create_item(conn: connection, player_name: str, item_name: str, item_value: int) -> str:
        """Attempts to create an item based on the player's craft skill."""
        result = get_craft_skill(conn, player_name)
        character_id = result.get('character_id')
        craft_skill = result.get('craft_skill')

        # Determine crafting success chance
        success_chance = min(
            (craft_skill / (item_value * 2)) * 100, 95)
        roll = randint(1, 100)

        if roll > success_chance:
            return f"{player_name}, your crafting attempt failed! Try again later."
        item_id = insert_item_player_inventory(
            conn, item_name, item_value, character_id)
        return f"{player_name.title()} successfully crafted '{item_name}' (Value: {item_value} {'shard' if item_value == 1 else 'shards'})!"


    async def setup(bot):
        """Sets up connection"""
        conn = bot.get_cog("Database").conn
        await bot.add_cog(Character(bot, conn))

