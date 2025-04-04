import discord
from discord.ext import commands
import discord.ext.commands
from psycopg2.extensions import connection
from bot.database_utils import DatabaseConnection
import discord.ext


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
        spell_details = {}
        spell_details["spell_name"] = spell_name
        if not ctx.author.guild_permissions.administrator:
            await ctx.send('❌ You must be an admin to use this command.')
            return

        if spell_name is None:
            await ctx.send("Usage: `!create_spell <spell_name>`")
            return

        message = await ctx.send(
            f"**Creating spell: {spell_name}**\nWould you like to create a **damage spell** or a **status spell**?"
        )

        view = StartCreationView(ctx, self.conn, spell_details)
        await message.edit(content="Choose an option:", view=view)


class StartCreationView(discord.ui.View):
    """Lets the user choose between a damage spell or status spell"""

    def __init__(self, ctx: commands.Context, conn: connection, spell_details: dict, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.conn = conn

        # Pass the arguments correctly to the button constructor
        self.add_item(SpellTypeButton("Damage Spell",
                                      "damage", ctx, conn, spell_details))
        self.add_item(SpellTypeButton("Status Spell",
                                      "status", ctx, conn, spell_details))


class SpellTypeButton(discord.ui.Button):
    """Button for choosing spell type"""

    def __init__(self, label: str, spell_type: str, ctx: commands.Context, conn: connection, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.blurple, label=label)
        self.spell_type = spell_type
        self.ctx = ctx
        self.conn = conn
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click"""
        await interaction.response.defer()

        await interaction.followup.send(f"You selected **{self.label}**.", ephemeral=True)
        self.spell_details['spell_type'] = self.spell_type

        if self.spell_type == "damage":
            await interaction.followup.send("How much power should the spell have?", view=PowerView(self.ctx, self.spell_details, self.conn), ephemeral=True)
        else:
            await interaction.followup.send("Choose a status effect:", view=StatusEffectView(self.ctx, self.conn, self.spell_details), ephemeral=True)


class StatusEffectView(discord.ui.View):
    """Lets the user select a status effect"""

    def __init__(self, ctx: commands.Context, conn: connection, spell_details: dict, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.conn = conn
        self.spell_details = spell_details

        status_effects = self.get_status_effects()
        for effect_id, effect_name in status_effects.items():
            self.add_item(StatusEffectButton(
                effect_name, effect_id, ctx, conn, self.spell_details))

    def get_status_effects(self):
        """Fetches available status effects from DB"""
        with self.conn.cursor() as cursor:
            query = "SELECT spell_status_id, status_name FROM spell_status;"
            cursor.execute(query)
            return {row['spell_status_id']: row['status_name'] for row in cursor.fetchall()}


class StatusEffectButton(discord.ui.Button):
    """Button to select a status effect"""

    def __init__(self, label: str, status_id: int, ctx: commands.Context, conn: connection, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.status_id = status_id
        self.ctx = ctx
        self.conn = conn
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles status effect selection"""
        await interaction.response.defer()
        await interaction.followup.send(f"Selected status effect: **{self.label}**. Now enter duration.", ephemeral=True)
        self.spell_details['spell_status_id'] = self.status_id
        print(f'status effect button {self.spell_details=}')
        await interaction.followup.send("Enter the duration of the effect (in turns):", view=DurationView(self.ctx, self.spell_details, self.conn), ephemeral=True)


class DurationView(discord.ui.View):
    """View for selecting the duration of a status effect spell."""

    def __init__(self, ctx, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = connection

        # Add duration buttons
        durations = [1, 2, 3, 4, 5]
        for duration in durations:
            self.add_item(DurationButton(duration, ctx, conn, self.spell_details))


class DurationButton(discord.ui.Button):
    """Button for selecting the duration of a status effect."""

    def __init__(self, duration: int, ctx: discord.ext.commands.Context, conn: connection, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{duration} turns")
        self.duration = duration
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click event."""

        self.spell_details['duration'] = self.duration
        print(f'DurationButton {self.spell_details=}')

        await interaction.response.defer()
        await interaction.followup.send(f"⏳ Status effect will last **{self.duration} turns**.")

        next_view = ChanceView(
            self.ctx, self.spell_details, self.conn)
        await interaction.followup.send("Next, choose the Chance of the status effect:", view=next_view, ephemeral=True)


class ChanceView(discord.ui.View):
    """View for selecting the probability of a status effect triggering."""

    def __init__(self, ctx, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

        # Add buttons for different chance percentages
        chances = [10, 25, 50, 75, 100]
        for chance in chances:
            self.add_item(ChanceButton(chance, conn, ctx, spell_details))
    

class ChanceButton(discord.ui.Button):
    """Button for selecting the status effect chance."""

    def __init__(self, chance: int, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.blurple,
                         label=f"{chance}% chance")
        self.chance = chance
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles the button click event."""
        try:
            self.spell_details['status_chance'] = self.chance
            print(f'ChanceButton {self.spell_details=}')

            await interaction.response.defer()
            await interaction.followup.send(f"🎲 Status effect will trigger **{self.chance}%** of the time.")

            # Move to Power Selection (since both damage and status spells have power)
            next_view = PowerView(self.ctx, self.spell_details, self.conn)
            await interaction.followup.send("Next, select the spell's power:", view=next_view, ephemeral=True)
        except Exception as e:
            print(e)


class PowerView(discord.ui.View):
    """View for selecting the spell's power level."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

        power_levels = [10, 30, 50, 70, 90, 110]
        for power in power_levels:
            self.add_item(PowerButton(power, conn, ctx, spell_details))


class PowerButton(discord.ui.Button):
    """Button for selecting spell power."""

    def __init__(self, power: int, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{power} Power")
        self.power = power
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        try:
            self.spell_details['power'] = self.power

            await interaction.response.defer()
            await interaction.followup.send(f"💥 Spell power set to **{self.power}**.")

            # Move to Mana Cost
            next_view = ManaCostView(self.ctx, self.spell_details, self.conn)
            await interaction.followup.send("Next, select the spell's mana cost:", view=next_view, ephemeral=True)
        except Exception as e:
            print(e)

class ManaCostView(discord.ui.View):
    """View for selecting the spell's mana cost."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

        mana_costs = [10, 20, 40, 60, 80, 100]
        for cost in mana_costs:
            self.add_item(ManaButton(cost, conn, ctx, spell_details))


class ManaButton(discord.ui.Button):
    """Button for selecting mana cost."""

    def __init__(self, cost: int, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(
            style=discord.ButtonStyle.primary, label=f"{cost} Mana")
        self.cost = cost
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""

        self.spell_details['mana_cost'] = self.cost
        print(f'ManaButton {self.spell_details=}')

        await interaction.response.defer()
        await interaction.followup.send(f"🔋 Mana cost set to **{self.cost}**.")

        # Move to Cooldown
        try:
            next_view = ElementView(self.ctx, self.spell_details, self.conn)
            await interaction.followup.send("Next, select the spell's Element:", view=next_view, ephemeral=True)
        except Exception as e:
            print(e)


class ElementView(discord.ui.View):
    """A View for selecting the spells element."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn
        element_map = self.get_element_map(conn)
        for element_name, element_id in element_map.items():
            self.add_item(ElementButton(
                element_name, element_id, conn, ctx, spell_details))

    def get_element_map(self, conn: connection) -> dict[str: int]:
        """gets a dictionary of {element_name: element_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT element_name, element_id
                        FROM element""")
            return {row['element_name']: row['element_id'] for row in cursor.fetchall()}

class ElementButton(discord.ui.Button):
    def __init__(self, element_name: str, element_id: int, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.blurple, label=element_name)
        self.element_name = element_name
        self.element_id = element_id
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details
    

    async def callback(self, interaction):
        """Handles button click event."""
        self.spell_details['element_name'] = self.element_name
        self.spell_details['element_id'] = self.element_id

        await interaction.response.defer()
        await interaction.followup.send(f"🔥 Element set to **{self.element_name}**.")

        next_view = CooldownView(self.ctx, self.spell_details, self.conn)
        await interaction.followup.send("Next, select the spell's cooldown:", view=next_view, ephemeral=True)

class CooldownView(discord.ui.View):
    """View for selecting the spell's cooldown."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

        cooldown = [1, 2, 3, 4, 5]
        for cd in cooldown:
            self.add_item(CooldownButton(cd, conn, ctx, spell_details))


class CooldownButton(discord.ui.Button):
    """Button for selecting cooldown."""

    def __init__(self, cooldown: int, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.primary,
                         label=f"{cooldown} Turns")
        self.cooldown = cooldown
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        self.spell_details['cooldown'] = self.cooldown
        print(f'CooldownButton {self.spell_details=}')

        await interaction.response.defer()
        await interaction.followup.send(f"⏳ Cooldown set to **{self.cooldown} turns**.")

        # Move to SpellTypeView

        next_view = SpellTypeView(self.ctx, self.spell_details, self.conn)
        await interaction.followup.send("Next, choose the spell type:", view=next_view, ephemeral=True)


class SpellTypeView(discord.ui.View):
    """View for selecting the spell type from the database."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

        # Fetch spell types and dynamically add buttons
        spell_types = self.fetch_spell_types()
        if spell_types:
            for spell_type_id, spell_type_name in spell_types.items():
                self.add_item(SpellTargetButton(
                    spell_type_id, spell_type_name, conn, ctx, spell_details))
        else:
            print("❌ No spell types found in the database.")


    def fetch_spell_types(self):
        """Fetch spell types from the database."""
        with self.conn.cursor() as cursor:
            query = "SELECT spell_type_id, spell_type_name FROM spell_type"
            cursor.execute(query)
            return {row['spell_type_id']: row['spell_type_name'] for row in cursor.fetchall()}


class SpellTargetButton(discord.ui.Button):
    """Button for selecting a spell type."""

    def __init__(self, spell_type_id: int, spell_type_name: str, conn: connection, ctx: commands.Context, spell_details: dict):
        super().__init__(style=discord.ButtonStyle.primary, label=spell_type_name)
        self.spell_type_id = spell_type_id
        self.spell_type_name = spell_type_name
        self.conn = conn
        self.ctx = ctx
        self.spell_details = spell_details

    async def callback(self, interaction: discord.Interaction):
        """Handles button click event."""
        self.spell_details['spell_type_id'] = self.spell_type_id
        self.spell_details['spell_type_name'] = self.spell_type_name

        await interaction.response.defer()
        await interaction.followup.send(f"🔮 Spell type set to **{self.spell_type_name}**.")

        # Move to Race/Class Exclusivity Selection
        next_view = ClassRaceView(self.ctx, self.spell_details, self.conn)
        await interaction.followup.send("Next, select race/class exclusivity:", view=next_view, ephemeral=True)


class ClassRaceView(discord.ui.View):
    """View for selecting either class or race exclusivity for a spell (mutually exclusive)."""

    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn
        eligible_casters = self.fetch_classes_and_races()
        for caster in eligible_casters:
            self.add_item(CasterButton(
                caster_type=caster["type"],
                caster_id=caster["id"],
                caster_name=caster["name"],
                spell_details=spell_details,
                ctx=ctx,
                conn=conn
            )
        )

    def fetch_classes_and_races(self) -> list[dict]:
        """Fetch available classes and races for this server."""
        server_id = self.ctx.guild.id
        with self.conn.cursor() as cursor:
            query = """SELECT 'class' AS table, class_id AS id, class_name AS name FROM class WHERE server_id = %s
                    UNION
                    SELECT 'race' AS table, race_id AS id, race_name AS name FROM race WHERE server_id = %s"""
            cursor.execute(query, (server_id, server_id)
                           )
            return [
                {
                    "type": row["table"],  # 'class' or 'race'
                    "id": row["id"],
                    "name": row["name"]
                }
                for row in cursor.fetchall()
            ]


class CasterButton(discord.ui.Button):
    """Confirms the race/class that can cast the spell"""
    def __init__(self, caster_type: str, caster_id: int, caster_name: str, spell_details: dict, ctx: commands.Context, conn: connection):
        super().__init__(label=caster_name, style=discord.ButtonStyle.red if caster_type ==
                         'class' else discord.ButtonStyle.green)
        self.caster_type = caster_type
        self.caster_id = caster_id
        self.caster_name = caster_name
        self.spell_details = spell_details
        self.ctx = ctx
        self.conn = conn


    async def callback(self, interaction: discord.Interaction):
        self.spell_details['caster_type'] = self.caster_type
        self.spell_details['caster_id'] = self.caster_id
        self.spell_details['caster_name'] = self.caster_name
        print(f'CasterButton {self.spell_details=}')
        await interaction.response.defer()
        await interaction.followup.send(f"Race/Class caster set to **{self.caster_name}**.")
        next_view = CreateSpell(self.ctx, self.spell_details, self.conn)
        await interaction.followup.send("Confirm?", view=next_view, ephemeral=True)


class CreateSpell(discord.ui.View):
    """View for confirming the spell to be created"""
    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection, timeout = 180):
        super().__init__(timeout=timeout)
        try:
            self.add_item(MakeSpell(ctx, spell_details, conn))
        except Exception as e:
            print(e)

class MakeSpell(discord.ui.Button):
    """Makes the spell and inserts it into the DB"""
    def __init__(self, ctx: commands.Context, spell_details: dict, conn: connection):
        super().__init__(style=discord.ButtonStyle.blurple, label='Confirm!')
        self.ctx = ctx
        self.spell_details = spell_details
        self.conn = conn

    async def callback(self, interaction: discord.Interaction):
        print('making spell:')
        try:
            class_id = None
            race_id = None
            if self.spell_details.get('caster_type') == 'class':
                class_id = self.spell_details.get('caster_id')
            else:
                race_id = self.spell_details.get('caster_id')
            spell_id = self.generate_spell(conn=self.conn,
                                       server_id=self.ctx.guild.id,
                                       spell_name=self.spell_details.get('spell_name', 'not found'),
                                       spell_description='TEMPORARY',
                                       spell_power=self.spell_details.get('power', 0),
                                       mana_cost=self.spell_details.get('mana_cost', 0),
                                       cooldown=self.spell_details.get('cooldown', 0),
                                       scaling_factor=1,
                                       spell_type_id=self.spell_details.get('spell_type_id'),
                                       element_id=self.spell_details.get('element_id'),
                                       spell_status_id=self.spell_details.get('spell_status_id', 1),
                                       spell_status_chance=self.spell_details.get('status_chance', 100),
                                       spell_duration= self.spell_details.get('duration', 1),
                                       race_id=race_id if race_id else None,
                                       class_id=class_id if class_id else None
                                       )
        
            await self.ctx.send(f'✨ Spell {self.spell_details.get('spell_name', 'not found')} has been created! as ID: {spell_id}')
        except Exception as e:
            print(e)
        return
    
    def generate_spell(self,
                       conn: connection,
                       server_id: int,
                       spell_name: str,
                       spell_description: str,
                       spell_power: int,
                       mana_cost: int,
                       cooldown: int,
                       scaling_factor: float,
                       spell_type_id: int,
                       element_id: int,
                       spell_status_id: int,
                       spell_status_chance: int,
                       spell_duration: int,
                       class_id: int = None,
                       race_id: int = None):
        """Inserts a new spell into the database and assigns its status."""
        print('generating spell!!!')
        try:
            with conn.cursor() as cursor:
                # Insert spell into spells table
                spell_sql = """
                INSERT INTO spells (spell_name, spell_description, spell_power, mana_cost, cooldown, scaling_factor, 
                                    spell_type_id, element_id, class_id, race_id, server_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                RETURNING spell_id;
                """
                spell_values = (spell_name,
                                spell_description,
                                spell_power,
                                mana_cost,
                                cooldown,
                                scaling_factor,
                                spell_type_id,
                                element_id,
                                class_id,
                                race_id,
                                server_id)

                cursor.execute(spell_sql, spell_values)
                spell_id = cursor.fetchone().get('spell_id')

                if spell_id is None:
                    conn.rollback()
                    return "❌ Error: Spell creation failed. Please try again."

                # Insert into spell_status_spell_assignment table
                status_sql = """
                INSERT INTO spell_status_spell_assignment (spell_id, spell_status_id, chance, duration)
                VALUES (%s, %s, %s, %s);
                """
                status_values = (spell_id, spell_status_id,
                                 spell_status_chance, spell_duration)

                cursor.execute(status_sql, status_values)

                # Commit transaction if everything is successful
                conn.commit()
            print(f"✨ Spell `{spell_name}` has been created!")
            return spell_id

        except Exception as e:
            conn.rollback()
            return f"❌ Error: {str(e)}"

async def setup(bot: commands.bot.Bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Spell(bot, conn))
