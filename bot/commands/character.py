"""Defines the Character commands

- !add_spell: adds a spell to the character to use in battle from a list of spells
- !spellbook: lets the player see the spells they have equipped
- !scavenge: lets the player get money from scavenging
- !craft: lets the player create a item that they can sell or enchant
- !inventory: lets the player view their inventory
"""
from random import randint
import re
from datetime import datetime, timedelta
import discord
from discord.ui import View, Button
from discord.ext import commands
from psycopg2.extensions import connection

from bot.database_utils import (DatabaseMapper,
                                DatabaseIDFetch,
                                InventoryDatabase,
                                EmbedHelper,
                                DataInserter,
                                DatabaseConnection)


class Character(commands.Cog):
    """Commands for managing player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print("Character cog loaded")

    @commands.command()
    async def create_character(self,
                               ctx: commands.Context,
                               character_name: str = None,
                               race_name: str = None,
                               class_name: str = None):
        """Creates a player character in the database"""
        player_map = DatabaseMapper.get_player_mapping(self.conn, ctx.guild.id)
        player_name = ctx.author.name
        if player_name in player_map.keys():
            player_id = player_map.get(player_name)
        else:
            player_id = DataInserter.create_player(ctx, self.conn)

        character_map = DatabaseMapper.get_character_mapping(
            self.conn, player_id)
        if character_name in character_map.keys():
            await ctx.send(f'{character_name} already exists, please choose a new name.')
            return

        race_map = DatabaseMapper.get_race_map(self.conn, ctx.guild.id)
        class_map = DatabaseMapper.get_class_map(self.conn, ctx.guild.id)
        race_id = race_map.get(race_name, None)
        class_id = class_map.get(class_name, None)
        if character_name and race_id and class_id:
            response = DataInserter.generate_character(
                self.conn, ctx, character_name, race_id, class_id, player_id)
            DataInserter.generate_events_for_character(
                self.conn, ctx.author.name)
            DataInserter.generate_inventory_for_character(
                self.conn, ctx.author.name)
            await ctx.send(response)
        else:
            await ctx.send("Invalid character name, race or class. ")

    @commands.command()
    async def add_spell(self, ctx: commands.Context):
        """Allows a player to assign a spell to their selected character"""
        player_spells = DatabaseMapper.get_potential_player_spells(
            self.conn, ctx)
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
                    name="Status Effect",
                    value=f"{status_name} ({chance}% for {duration} turns)", inline=False)

            embed.set_footer(text=f"Spell ID: {spell_id}")

            await ctx.send(embed=embed)

        # Ask for the player's input
        await ctx.send("Reply with the Spell ID of the spell you want to learn.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            selected_spell_id = int(msg.content)

            if selected_spell_id not in spell_id_list:
                await ctx.send("Invalid Spell ID. Please try again.")
                return

            DataInserter.add_spell_to_character(
                self.conn, ctx, selected_spell_id)

            await ctx.send(f"Spell {selected_spell_id} has been added to your character!")

        except TimeoutError:
            await ctx.send("⏳ You took too long to respond. Try again.")

    @commands.command()
    async def spellbook(self, ctx: commands.Context):
        """Checks the equipped spells"""
        equipped_spells = DatabaseMapper.get_equipped_spells(self.conn, ctx)
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

    @commands.command()
    async def scavenge(self, ctx: commands.Context):
        """allows the player to scavenge for money"""

        last_scavenged = DatabaseMapper.get_last_event(
            self.conn, ctx.author.name, 'Scavenge')


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
            message = DataInserter.increase_wallet(
                self.conn, ctx.author.name, profit)
            DataInserter.update_last_event(
                self.conn, ctx.author.name, 'Scavenge', now)

            await ctx.send(message)
        else:
            await ctx.send(f"{ctx.author.display_name}, you need to create a character first!")

    @commands.command()
    async def craft(self, ctx: commands.Context, item_name: str = None, item_value: int = None):
        """Lets a player craft an item"""
        # Get the last crafted time for the player
        if not item_name or not item_value:
            await ctx.send('Usage !craft <item_name> <item_value>')
            return

        last_crafted = DatabaseMapper.get_last_event(
            self.conn, ctx.author.name, 'Craft')

        if last_crafted:
            # Calculate the time difference from the last crafted event
            time_since_last = datetime.now() - last_crafted
            # If the player crafted in the last 3 hours, block the crafting
            if time_since_last < timedelta(hours=3):
                await ctx.send(f"You can't craft right now. Please wait {3 - time_since_last.seconds // 3600} hour(s) before crafting again.")
                return

            # If the player hasn't crafted recently, proceed with creating the item
            message = self.create_item(
                self.conn, ctx.author.name, item_name, item_value)
            await ctx.send(message)
        else:
            await ctx.send('Please make a character using !create_character <race> <class>')


    @commands.command()
    async def inventory(self, ctx: commands.Context):
        """Shows the player their inventory in an embed"""

        # Get character_id for the player
        character_id = DatabaseIDFetch.fetch_selected_character_id(self.conn, ctx.author.name)
        if not character_id:
            await ctx.send("No character selected for this player.")
            return

        # Get inventory_id for the character
        inventory_id = DatabaseIDFetch.get_inventory_id(
            self.conn, character_id)
        if not inventory_id:
            await ctx.send("This character does not have an inventory.")
            return

        # Get items in the inventory
        items = InventoryDatabase.get_items_in_inventory(
            self.conn, inventory_id)
        if not items:
            await ctx.send("Your inventory is empty.")
            return

        # Create the embed and send it
        embed = EmbedHelper.create_inventory_embed(ctx, items)
        await ctx.send(embed=embed)


    def create_item(self, conn: connection, player_name: str, item_name: str, item_value: int) -> str:
        """Attempts to create an item based on the player's craft skill."""
        DataInserter.update_last_event(conn, player_name, 'Craft', datetime.now())
        result = DatabaseMapper.get_craft_skill(conn, player_name)
        character_id = result.get('character_id')
        craft_skill = result.get('craft_skill')

        # Determine crafting success chance
        success_chance = min(
            (craft_skill / (item_value * 2)) * 100, 95)
        roll = randint(1, 100)

        if roll > success_chance:
            return f"{player_name}, your crafting attempt failed! Try again later."
        item_id = DataInserter.insert_item_player_inventory(
            conn, item_name, item_value, character_id)
        return f"{player_name.title()} successfully crafted '{item_name}' (Value: {item_value} {'shard' if item_value == 1 else 'shards'})!"


    def validate_image_url(self, image_url: str) -> bool:
        """Validates an image URL"""
        pattern = r'https?://.*\.(?:jpg|jpeg|png|svg)'
        return True if re.match(pattern, image_url, re.IGNORECASE) else False


    @commands.command()
    async def character_image(self, ctx: commands.Context, image_url: str = None):
        """Allows the player to associate an image with their character using a URL to a hosted image file"""
        print('running character_image')
        if image_url:
            print(image_url)
            valid = self.validate_image_url(image_url)
            print(valid)
            if valid:
                print('is valid image')
        elif ctx.message.attachments:
            image_url = ctx.message.attachments[0].url
            print(image_url)
            valid = self.validate_image_url(image_url)
        else:
            valid = False

        if not valid:
            await ctx.send("Please send a valid image URL or attach an image!")
            return

        # Call the DataInserter method properly
        DataInserter.add_character_image(self.conn, ctx.author.name, image_url)
        await ctx.send("Character image has been updated successfully!")

    @commands.command()
    async def quick_sell(self, ctx: commands.Context):
        """Allows a player to quickly sell items from their inventory."""

        # Get character_id for the player
        character_id = DatabaseIDFetch.fetch_selected_character_id(
            self.conn, ctx.author.name)
        if not character_id:
            await ctx.send("No character selected for this player.")
            return

        # Get inventory_id for the character
        inventory_id = DatabaseIDFetch.get_inventory_id(
            self.conn, character_id)
        if not inventory_id:
            await ctx.send("This character does not have an inventory.")
            return

        # Get items in the inventory
        items = InventoryDatabase.get_items_in_inventory(
            self.conn, inventory_id)
        if not items:
            await ctx.send("Your inventory is empty.")
            return

        # Create an embed for each item with a Sell Button
        for item in items:
            item_name = item.get('item_name')
            item_id = item.get('item_id')
            spell_name = item.get('spell_name', 'None')  # Optional field
            value = item.get('value', 0)

            embed = discord.Embed(
                title=item_name.title(),
                description=f"**ID:** {item_id}\n**Spell:** {spell_name}\n**Value:** {value} shards",
                color=discord.Color.green()
            )

            view = View()
            view.add_item(SellItemButton(item_id, item_name, value, self.conn))

            await ctx.send(embed=embed, view=view)
    

    @commands.command()
    async def sell(self, ctx: commands.Context):
        # Get character_id for the player
        character_id = DatabaseIDFetch.fetch_selected_character_id(
            self.conn, ctx.author.name)
        if not character_id:
            await ctx.send("No character selected for this player.")
            return

        # Get inventory_id for the character
        inventory_id = DatabaseIDFetch.get_inventory_id(
            self.conn, character_id)
        if not inventory_id:
            await ctx.send("This character does not have an inventory.")
            return

        # Get items in the inventory
        items = InventoryDatabase.get_items_in_inventory(
            self.conn, inventory_id)
        if not items:
            await ctx.send("Your inventory is empty.")
            return

        # Create and send embeds for each item in the inventory
        for item in items:
            item_name = item.get('item_name')
            item_id = item.get('item_id')
            spell_name = item.get('spell_name', 'None')  # Not currently being queried
            value = item.get('value', 0)

            embed = discord.Embed(
                title=item_name.title(),
                description=f"**ID:** {item_id}\n**Spell:** {spell_name}\n**Value:** {value} shards",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        await ctx.send('Select the id of the item you want to sell and its value')

        def check(m):
            # Ensure the message contains item ID and value
            parts = m.content.split()
            return m.author == ctx.author and m.channel == ctx.channel and len(parts) == 2 and all(part.isdigit() for part in parts)

        try:
            # Wait for the player's response
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            item_id, value = msg.content.split()
            item_id = int(item_id)
            value = int(value)

            # Check if the item exists in the inventory
            if item_id not in [item.get('item_id') for item in items]:
                await ctx.send('Select a listed item')
                return

            # Set the item as sellable in the database
            success = InventoryDatabase.set_sellable_item(
                self.conn, item_id, value)
            if success:
                # Find the item name for the confirmation message
                item_name = next(item.get('item_name')
                                for item in items if item.get('item_id') == item_id)
                await ctx.send(f"✅ Listed {item_name} for {value} shards!")
            else:
                await ctx.send("⚠️ Could not list the item!")

        except TimeoutError:
            await ctx.send("⏳ You took too long to respond. Try again.")
        except ValueError:
            await ctx.send("⚠️ Please provide both an item ID and a value separated by a space.")

    @commands.command()
    async def marketplace(self, ctx: commands.Context):
        """Prints the marketplace"""
        items = InventoryDatabase.get_marketplace(self.conn)
        # Create an embed for each item with a Sell Button
        for item in items:
            print(item)
            item_name = item.get('item_name')
            item_id = item.get('item_id')
            spell_name = item.get('spell_name', 'None')  # Not currently working
            value = item.get('listed_value', 0)
            player_name = item.get('player_name')
            character_name = item.get('character_name')

            embed = discord.Embed(
                title=item_name.title(),
                description=f"**ID:** {item_id}\n**Spell:** {spell_name}\n**Value:** {value} shards",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Sold by", value=f"{player_name} as {character_name}")

            view = View()
            view.add_item(BuyItemButton(item_id, item_name, player_name, value, self.conn))

            await ctx.send(embed=embed, view=view)


async def setup(bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Character(bot, conn))


class SellItemButton(Button):
    def __init__(self, item_id: int, item_name: str, value: int, conn):
        super().__init__(label=f"Sell {item_name}",
                         style=discord.ButtonStyle.red)
        self.item_id = item_id
        self.item_name = item_name
        self.value = value
        self.conn = conn

    async def callback(self, interaction: discord.Interaction):
        # Sell the item (remove from inventory and add shards)
        success = InventoryDatabase.sell_item(
            self.conn, self.item_id, interaction.user.name)

        if success:
            await interaction.response.edit_message(content=f"✅ Sold {self.item_name} for {self.value} shards!", embed=None, view=None)
        else:
            await interaction.response.edit_message(content="⚠️ Could not sell the item!", embed=None, view=None)


class BuyItemButton(Button):
    def __init__(self, item_id: int, item_name: str, player_name, value: int, conn):
        super().__init__(label=f"Buy {item_name}",
                         style=discord.ButtonStyle.red)
        self.item_id = item_id
        self.item_name = item_name
        self.player_name = player_name
        self.value = value
        self.conn = conn

    async def callback(self, interaction: discord.Interaction):
        # Sell the item (remove from inventory and add shards)
        success = InventoryDatabase.buy_item(
            self.conn, self.item_id, self.player_name, interaction.user.name, self.value)

        if success:
            await interaction.response.edit_message(content=f"✅ Sold {self.item_name} for {self.value} shards!", embed=None, view=None)
        else:
            await interaction.response.edit_message(content="⚠️ Could not Buy the item!", embed=None, view=None)
