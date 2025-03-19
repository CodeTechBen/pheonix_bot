"""commands that refer to spells
- !create_spell: Lets an Admin create a spell
"""

import discord
from discord.ext import commands
from psycopg2.extensions import connection

from bot.database_utils import (DatabaseMapper,
                                EmbedHelper,
                                DataInserter,
                                DatabaseConnection,
                                UserInputHelper)


# class Spell(commands.Cog):
#     """Defines the commands that allow for the creation, addition or usage of spells"""
#     def __init__(self, bot: commands.bot.Bot, conn: connection):
#         self.bot = bot
#         self.conn = conn
#         print('Spell cog loaded')

#     @commands.command()
#     async def create_spell(self, ctx: commands.Context):
#         """Command to generate a spell"""
#         if not ctx.author.guild_permissions.administrator:
#             await ctx.send('You must be an admin to use this command.')
#             return

#         spell_name = await UserInputHelper.get_input(ctx, self.bot, "📝 Enter the spell name:")
#         if not spell_name:
#             return

#         spell_description = await UserInputHelper.get_input(
#             ctx, self.bot, "📖 Enter spell description:")
#         if not spell_description:
#             return

#         spell_power = await UserInputHelper.get_input(
#             ctx, self.bot, "💥 Enter spell power (1-100):", int)
#         if spell_power is None:
#             return

#         mana_cost = await UserInputHelper.get_input(
#             ctx, self.bot, "🔋 Enter mana cost:", int)
#         if mana_cost is None:
#             return

#         cooldown = await UserInputHelper.get_input(
#             ctx, self.bot, "⏳ Enter cooldown (in turns):", int, True)
#         if cooldown is None:
#             return

#         scaling_factor = await UserInputHelper.get_input(
#             ctx, self.bot, "🎚️ Enter scaling factor (0.1 - 2.0):", float)
#         if scaling_factor is None:
#             return

#         # Fetch spell types
#         spell_types = DatabaseMapper.get_spell_type_map(self.conn)
#         if not spell_types:
#             await ctx.send("❌ No spell types found in the database.")
#             return

#         await ctx.send(embed=EmbedHelper.create_map_embed(
#             "📜 Spell Types", "Available spell types:", spell_types, discord.Color.blue()))
#         spell_type_id = await UserInputHelper.get_input(
#             ctx, self.bot, "⚡ Enter the **ID** of the spell type:", int)

#         if spell_type_id is None or spell_type_id not in spell_types:
#             await ctx.send("❌ Invalid spell type ID. Try again.")
#             return

#         # Fetch Elements
#         element_map = DatabaseMapper.get_element_map(self.conn)
#         await ctx.send(embed=EmbedHelper.create_map_embed(
#             "🔥 Elements", "Available Elements", element_map, discord.Color.red()))
#         element_id = await UserInputHelper.get_input(
#             ctx, self.bot, "🔥 Enter the **ID** of the element:", int)

#         # Fetch available classes
#         classes = DatabaseMapper.get_class_map(self.conn, ctx.guild.id)
#         await ctx.send(embed=EmbedHelper.create_map_embed(
#             "🛡️ Classes", "Available classes:", classes, discord.Color.green()))
#         class_id = await UserInputHelper.get_input(
#             ctx, self.bot, "⚔️ Enter the **ID** of the class (or `0` if none):", int, True)
#         class_id = None if class_id == 0 else class_id

#         # Fetch available races
#         races = DatabaseMapper.get_race_map(self.conn, ctx.guild.id)
#         await ctx.send(embed=EmbedHelper.create_map_embed(
#             "🧬 Races", "Available races:", races, discord.Color.purple()))
#         race_id = await UserInputHelper.get_input(
#             ctx, self.bot, "🧬 Enter the **ID** of the race (or `0` if none):", int, True)
#         race_id = None if race_id == 0 else race_id

#         # Fetch spell statuses
#         spell_statuses = DatabaseMapper.get_spell_status_map(self.conn)
#         await ctx.send(embed=EmbedHelper.create_map_embed("🌀 Spell Status Effects",
#                                           "Available status effects:",
#                                           spell_statuses,
#                                           discord.Color.purple()))
#         spell_status_id = await UserInputHelper.get_input(
#             ctx, self.bot, "🌀 Enter the **ID** of the spell status effect:", int, True)
#         spell_status_chance = await UserInputHelper.get_input(
#             ctx, self.bot, r"% chance of status condition!", int, True)
#         spell_duration = await UserInputHelper.get_input(
#             ctx, self.bot, "Duration of status condition (in turns)", int)

#         # Generate the spell
#         spell_id = DataInserter.generate_spell(
#             self.conn, ctx.guild.id, spell_name, spell_description, spell_power,
#             mana_cost, cooldown, scaling_factor, spell_type_id, element_id,
#             spell_status_id, spell_status_chance, spell_duration, class_id, race_id
#         )
#         await ctx.send(f'✨ Spell {spell_name} has been created! as ID: {spell_id}')
    
############################################################################################################
class Spell(commands.Cog):
    """Defines spell-related commands"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print('Spell cog loaded')


    @commands.command()
    async def create_spell(self, ctx: commands.Context, spell_name: str = None):
        """Starts the spell creation process with a given spell name"""
        print(f'create_spell {spell_name=}')
        if not ctx.author.guild_permissions.administrator:
            await ctx.send('❌ You must be an admin to use this command.')
            return

        if spell_name is None:
            await ctx.send("Usage: `!create_spell <spell_name>`")
            return

        message = await ctx.send(
            f"**Creating spell: {spell_name}**\nWould you like to create a **damage spell** or a **status spell**?"
        )

        view = StartCreationView(ctx, self.conn, spell_name)
        await message.edit(content="Choose an option:", view=view)


class StartCreationView(discord.ui.View):
    """Lets the user choose between a damage spell or status spell"""

    def __init__(self, ctx: commands.Context, conn: connection, spell_name: str, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.conn = conn

        # Pass the arguments correctly to the button constructor
        self.add_item(SpellTypeButton("Damage Spell",
                        "damage", ctx, conn, spell_name))
        self.add_item(SpellTypeButton("Status Spell",
                        "status", ctx, conn, spell_name))



class SpellTypeButton(discord.ui.Button):
    """Button for choosing spell type"""

    def __init__(self, label: str, spell_type: str, ctx: commands.Context, conn: connection, spell_name: str):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.spell_type = spell_type
        self.ctx = ctx
        self.conn = conn
        self.spell_name = spell_name

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click"""
        await interaction.response.defer()

        await interaction.followup.send(f"You selected **{self.label}**.", ephemeral=True)

        if self.spell_type == "damage":
            await interaction.followup.send("How much power should the spell have?", view=PowerView(self.ctx, self.conn), ephemeral=True)
        else:
            await interaction.followup.send("Choose a status effect:", view=StatusEffectView(self.ctx, self.conn), ephemeral=True)


class StatusEffectView(discord.ui.View):
    """Lets the user select a status effect"""

    def __init__(self, ctx: commands.Context, conn, *, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.conn = conn

        status_effects = self.get_status_effects()
        for effect_id, effect_name in status_effects.items():
            self.add_item(StatusEffectButton(
                effect_name, effect_id, ctx, conn))

    def get_status_effects(self):
        """Fetches available status effects from DB"""
        with self.conn.cursor() as cursor:
            query = "SELECT spell_status_id, status_name FROM spell_status;"
            cursor.execute(query)
            return {row['spell_status_id']: row['status_name'] for row in cursor.fetchall()}


class StatusEffectButton(discord.ui.Button):
    """Button to select a status effect"""

    def __init__(self, label: str, status_id: int, ctx: commands.Context, conn):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.status_id = status_id
        self.ctx = ctx
        self.conn = conn

    async def callback(self, interaction: discord.Interaction):
        """Handles status effect selection"""
        await interaction.response.defer()
        await interaction.followup.send(f"Selected status effect: **{self.label}**. Now enter duration.", ephemeral=True)
        spell_data = {}
        spell_data['spell_status'] = self.status_id
        await interaction.followup.send("Enter the duration of the effect (in turns):", view=DurationView(self.ctx, spell_data, self.conn))


class DurationView(discord.ui.View):
    """View for selecting the duration of a status effect spell."""

    def __init__(self, ctx, spell_data: dict, conn: connection timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data
        self.conn = connection

        # Add duration buttons
        durations = [1, 2, 3, 4, 5]
        for duration in durations:
            self.add_item(DurationButton(duration, conn))


class DurationButton(discord.ui.Button):
    """Button for selecting the duration of a status effect."""

    def __init__(self, duration, conn):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{duration} turns")
        self.duration = duration

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click event."""

        spell_data = self.view.spell_data
        spell_data['duration'] = self.duration  # Store the duration

        await interaction.response.defer()
        await interaction.followup.send(f"⏳ Status effect will last **{self.duration} turns**.")

        # Proceed to next step (e.g., setting spell power, element, etc.)
        try:
            next_view = ChanceView(self.view.ctx, spell_data)
        except Exception as e:
            print(e)
        await interaction.followup.send("Next, choose the Chance of the status effect:", view=next_view)


class ChanceView(discord.ui.View):
    """View for selecting the probability of a status effect triggering."""

    def __init__(self, ctx, spell_data, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data  # Dictionary to store spell details

        # Add buttons for different chance percentages
        chances = [10, 25, 50, 75, 100]
        for chance in chances:
            self.add_item(ChanceButton(chance))


class ChanceButton(discord.ui.Button):
    """Button for selecting the status effect chance."""

    def __init__(self, chance):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{chance}% chance")
        self.chance = chance

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click event."""
        try:
            spell_data = self.view.spell_data
            # Store the chance percentage
            spell_data['status_chance'] = self.chance

            await interaction.response.defer()
            await interaction.followup.send(f"🎲 Status effect will trigger **{self.chance}%** of the time.")

            # Move to Power Selection (since both damage and status spells have power)
            next_view = PowerView(self.view.ctx, spell_data)
            await interaction.followup.send("Next, select the spell's power:", view=next_view)
        except Exception as e:
            print(e)

class PowerView(discord.ui.View):
    """View for selecting the spell's power level."""

    def __init__(self, ctx, spell_data, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data

        power_levels = [10, 30, 50, 70, 90, 110]
        for power in power_levels:
            self.add_item(PowerButton(power))


class PowerButton(discord.ui.Button):
    """Button for selecting spell power."""

    def __init__(self, power):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{power} Power")
        self.power = power

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        spell_data = self.view.spell_data
        spell_data['power'] = self.power

        await interaction.response.defer()
        await interaction.followup.send(f"💥 Spell power set to **{self.power}**.")

        # Move to Mana Cost
        next_view = ManaCostView(self.view.ctx, spell_data)
        await interaction.followup.send("Next, select the spell's mana cost:", view=next_view)


class ManaCostView(discord.ui.View):
    """View for selecting the spell's mana cost."""

    def __init__(self, ctx, spell_data, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data

        mana_costs = [10, 20, 40, 60, 80, 100]
        for cost in mana_costs:
            self.add_item(ManaButton(cost))


class ManaButton(discord.ui.Button):
    """Button for selecting mana cost."""

    def __init__(self, cost):
        super().__init__(
            style=discord.ButtonStyle.primary, label=f"{cost} Mana")
        self.cost = cost

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        spell_data = self.view.spell_data
        spell_data['mana_cost'] = self.cost

        await interaction.response.defer()
        await interaction.followup.send(f"🔋 Mana cost set to **{self.cost}**.")

        # Move to Cooldown
        next_view = CooldownView(self.view.ctx, spell_data)
        await interaction.followup.send("Next, select the spell's cooldown:", view=next_view)


class CooldownView(discord.ui.View):
    """View for selecting the spell's cooldown."""

    def __init__(self, ctx, spell_data, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data

        cooldowns = [1, 2, 3, 4, 5]
        for cd in cooldowns:
            self.add_item(CooldownButton(cd))


class CooldownButton(discord.ui.Button):
    """Button for selecting cooldown."""

    def __init__(self, cooldown):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{cooldown} Turns")
        self.cooldown = cooldown

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        spell_data = self.view.spell_data
        spell_data['cooldown'] = self.cooldown

        await interaction.response.defer()
        await interaction.followup.send(f"⏳ Cooldown set to **{self.cooldown} turns**.")

        # Move to SpellTypeView
        try:
            next_view = SpellTypeView(self.view.ctx, spell_data, conn)
        except Exception as e:
            print(e)
        await interaction.followup.send("Next, choose the spell type:", view=next_view)


class SpellTypeView(discord.ui.View):
    """View for selecting the spell type from the database."""

    def __init__(self, ctx, spell_data, conn, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data  # Store spell details
        self.conn = conn  # Database connection

    async def fetch_spell_types(self):
        """Fetch spell types from the database."""
        async with self.conn.acquire() as conn:
            query = "SELECT spell_type_id, spell_type_name FROM spell_type"
            rows = await conn.fetch(query)
            return rows

    async def start(self, interaction: discord.Interaction):
        """Dynamically add spell type buttons."""
        spell_types = await self.fetch_spell_types()

        if not spell_types:
            await interaction.response.send_message("❌ No spell types found in the database.")
            return

        for spell_type in spell_types:
            spell_type_id, spell_type_name = spell_type["spell_type_id"], spell_type["spell_type_name"]
            self.add_item(SpellTargetButton(
                spell_type_id, spell_type_name))

        await interaction.response.edit_message(content="Select the spell type:", view=self)


class SpellTargetButton(discord.ui.Button):
    """Button for selecting a spell type."""

    def __init__(self, spell_type_id, spell_type_name):
        super().__init__(style=discord.ButtonStyle.primary, label=spell_type_name)
        self.spell_type_id = spell_type_id
        self.spell_type_name = spell_type_name

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        spell_data = self.view.spell_data
        spell_data['spell_type_id'] = self.spell_type_id
        spell_data['spell_type_name'] = self.spell_type_name

        await interaction.response.defer()
        await interaction.followup.send(f"🔮 Spell type set to **{self.spell_type_name}**.")

        # Move to Race/Class Exclusivity Selection
        next_view = ClassRaceView(self.view.ctx, spell_data, self.view.conn)
        await interaction.followup.send("Next, select race/class exclusivity:", view=next_view)


class ClassRaceView(discord.ui.View):
    """View for selecting either class or race exclusivity for a spell (mutually exclusive)."""

    def __init__(self, ctx, spell_data, conn, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data  # Store spell details
        self.conn = conn  # Database connection
        self.selected_class = None
        self.selected_race = None

    async def fetch_classes_and_races(self):
        """Fetch available classes and races for this server."""
        server_id = self.ctx.guild.id
        async with self.conn.acquire() as conn:
            classes = await conn.fetch("SELECT class_id, class_name FROM class WHERE server_id = $1", server_id)
            races = await conn.fetch("SELECT race_id, race_name FROM race WHERE server_id = $1", server_id)
        return classes, races

    async def start(self, interaction: discord.Interaction):
        """Creates selection menus for class or race exclusivity dynamically."""
        classes, races = await self.fetch_classes_and_races()

        if not classes and not races:
            await interaction.response.send_message("❌ No classes or races found for this server.")
            return

        if classes:
            self.add_item(ClassSelectMenu(classes))
        if races:
            self.add_item(RaceSelectMenu(races))

        self.add_item(FinishSelectionButton())
        await interaction.response.edit_message(content="Select **either** a class or a race for exclusivity:", view=self)


class ClassSelectMenu(discord.ui.Select):
    """Dropdown menu for selecting a class (mutually exclusive)."""

    def __init__(self, classes):
        options = [discord.SelectOption(
            label=cls["class_name"], value=str(cls["class_id"])) for cls in classes]
        super().__init__(placeholder="Select a class (or leave blank for race exclusivity)",
                         min_values=0, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        """Handles class selection, disabling race selection if chosen."""
        self.view.selected_class = self.values[0] if self.values else None
        self.view.selected_race = None  # Ensure mutual exclusivity
        await interaction.response.defer()


class RaceSelectMenu(discord.ui.Select):
    """Dropdown menu for selecting a race (mutually exclusive)."""

    def __init__(self, races):
        options = [discord.SelectOption(
            label=race["race_name"], value=str(race["race_id"])) for race in races]
        super().__init__(placeholder="Select a race (or leave blank for class exclusivity)",
                         min_values=0, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        """Handles race selection, disabling class selection if chosen."""
        self.view.selected_race = self.values[0] if self.values else None
        self.view.selected_class = None  # Ensure mutual exclusivity
        await interaction.response.defer()


class FinishSelectionButton(discord.ui.Button):
    """Button to confirm exclusivity and move to the next step."""

    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="Confirm Selection")

    async def callback(self, interaction: discord.Interaction):
        """Finalizes the exclusivity selection and moves to the next step."""
        spell_data = self.view.spell_data

        if self.view.selected_class:
            spell_data['class_id'] = self.view.selected_class
            spell_data['race_id'] = None
            confirmation_msg = f"✅ Spell is exclusive to **class** <@&{self.view.selected_class}>."
        elif self.view.selected_race:
            spell_data['race_id'] = self.view.selected_race
            spell_data['class_id'] = None
            confirmation_msg = f"✅ Spell is exclusive to **race** <@&{self.view.selected_race}>."
        else:
            confirmation_msg = "❌ No class or race was selected. The spell is available would be available to None."
            return

        await interaction.response.defer()
        await interaction.followup.send(confirmation_msg)

        # Move to Element Selection
        next_view = ElementView(self.view.ctx, spell_data, self.view.conn)
        await interaction.followup.send("Next, select the spell's element:", view=next_view)


class ElementView(discord.ui.View):
    """View for selecting the element of the spell."""

    def __init__(self, ctx, spell_data, conn, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_data = spell_data  # Store spell details
        self.conn = conn  # Database connection

    async def fetch_elements(self):
        """Fetch available elements from the database."""
        async with self.conn.acquire() as conn:
            elements = await conn.fetch("SELECT element_id, element_name FROM element")
        return elements

    async def start(self, interaction: discord.Interaction):
        """Creates a dropdown for element selection dynamically."""
        elements = await self.fetch_elements()

        if not elements:
            await interaction.response.send_message("❌ No elements found in the database.")
            return

        self.add_item(ElementSelectMenu(elements, self))
        self.add_item(FinishElementSelectionButton(self))
        await interaction.response.edit_message(content="Select the **element** for this spell:", view=self)


class ElementSelectMenu(discord.ui.Select):
    """Dropdown menu for selecting an element."""

    def __init__(self, elements, view):
        options = [discord.SelectOption(label=elem["element_name"], value=str(
            elem["element_id"])) for elem in elements]
        super().__init__(placeholder="Select an element",
                         min_values=1, max_values=1, options=options)
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        """Handles element selection."""
        self.view.spell_data['element_id'] = self.values[0]
        await interaction.response.defer()


class FinishElementSelectionButton(discord.ui.Button):
    """Button to confirm element selection and finalize spell creation."""

    def __init__(self, view):
        super().__init__(style=discord.ButtonStyle.success, label="Confirm Element")
        self.view = view

    async def callback(self, interaction: discord.Interaction):
        """Finalizes element selection and saves spell data."""
        spell_data = self.view.spell_data

        if "element_id" in spell_data:
            confirmation_msg = f"✅ Spell element set to <@&{spell_data['element_id']}>."
        else:
            confirmation_msg = "❌ No element selected. Defaulting to **Neutral**."

        await interaction.response.defer()
        await interaction.followup.send(confirmation_msg)

        # Spell creation complete - Here you might insert into the database
        await self.save_spell(spell_data, interaction)

    async def save_spell(self, spell_data, interaction):
        """Inserts the spell into the database."""
        async with self.view.conn.acquire() as conn:
            await conn.execute("""
                INSERT INTO spell (spell_name, power, mana_cost, cooldown, spell_type_id, class_id, race_id, element_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, spell_data["spell_name"], spell_data["power"], spell_data["mana_cost"], spell_data["cooldown"],
                spell_data["spell_type_id"], spell_data.get("class_id"), spell_data.get("race_id"), spell_data["element_id"])

        await interaction.followup.send("✅ Spell successfully created!")


async def setup(bot: commands.bot.Bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Spell(bot, conn))
