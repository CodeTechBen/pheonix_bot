"""Creates a character for a player"""
import discord
from discord.ext import commands
from discord import ui
from psycopg2.extensions import connection
from bot.database_utils import DatabaseConnection


class CharacterCreation(commands.Cog):
    """Character creation object"""

    def __init__(self, bot: commands.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        self.races = {}
        self.classes = {}
        self.character_name = ""
        print('Character Creation cog loaded')

    @commands.command()
    async def character(self, ctx: commands.Context):
        """Lets the player create or select a character"""
        # Send the initial message with selection buttons
        message = await ctx.send(
            "Would you like to create a new character or select an existing one?",
            ephemeral=True
        )
        # Add the Select and Create buttons
        view = CharacterSelectView(self, ctx)
        await message.edit(view=view)

    def get_race_dict(self, ctx: commands.Context):
        """Fetches and returns a dictionary of race ids and names."""
        query = "SELECT race_id, race_name FROM race"
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            races = cursor.fetchall()

        # Convert the result into a dictionary
        return {race['race_id']: race['race_name'] for race in races}

    def get_class_dict(self, ctx: commands.Context):
        """Fetches and returns a dictionary of class ids and names."""
        query = "SELECT class_id, class_name FROM class"
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            classes = cursor.fetchall()

        # Convert the result into a dictionary
        return {cls['class_id']: cls['class_name'] for cls in classes}


class CharacterSelectView(ui.View):
    """View that presents options to the player to either create a new character or select an existing one"""

    def __init__(self, cog: CharacterCreation, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.ctx = ctx

        # Add buttons for character creation and selection
        self.add_item(CharacterCreateButton(self.ctx, self.cog))
        self.add_item(CharacterSelectButton(self.ctx, self.cog))


class CharacterCreateButton(ui.Button):
    """Button to create a new character"""

    def __init__(self, ctx: commands.Context, cog: CharacterCreation):
        super().__init__(style=discord.ButtonStyle.green, label="Create Character")
        self.ctx = ctx
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        """Handles the character creation process"""
        await interaction.response.defer()

        # Prompt the user to enter a character name
        await interaction.followup.send(
            "Please provide a name for your new character:", ephemeral=True
        )

        # Wait for the user to provide the character name
        def check(message):
            return message.author == self.ctx.author and message.channel == self.ctx.channel

        msg = await self.ctx.bot.wait_for("message", check=check)
        self.cog.character_name = msg.content.strip()
        print(msg.content.strip())

        self.cog.races = self.cog.get_race_dict(self.ctx)
        self.cog.classes = self.cog.get_class_dict(self.ctx)

        message = await self.ctx.send(
            f"Please select a race for {self.cog.character_name}.",
            ephemeral=True
        )
        view = RaceSelect(self.cog, self.ctx, message,
                          self.cog.races, self.cog.classes)
        await interaction.followup.send(f"Select a race for {self.cog.character_name}.", view=view, ephemeral=True)


class CharacterSelectButtonItem(ui.Button):
    """Button to select an existing character"""

    def __init__(self, ctx: commands.Context, cog: CharacterCreation, character_name: str, character_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, label=character_name)
        self.ctx = ctx
        self.cog = cog
        self.character_name = character_name
        self.character_id = character_id

    async def callback(self, interaction: discord.Interaction):
        """Handles selecting an existing character"""
        await interaction.response.defer()

        # Query to get the player_id based on the player_name
        query_player_id = """
            SELECT player_id
            FROM player
            WHERE player_name = %s;
        """
        with self.cog.conn.cursor() as cursor:
            cursor.execute(query_player_id, (self.ctx.author.name,))
            player_result = cursor.fetchone()

        player_id = player_result['player_id']
        # Update the character selection process
        success = self.select_new_character(
            player_id, self.ctx.guild.id, self.character_id)

        if success:
            # Successfully updated the selected character
            await interaction.followup.send(
                f"You have selected {self.character_name}!", ephemeral=True
            )
        else:
            # There was an error with the selection process
            await interaction.followup.send(
                "There was an error while selecting your character. Please try again.", ephemeral=True
            )

    def select_new_character(self, player_id, server_id, character_id):
        """Handles the logic for updating the selected character in the database"""
        with self.cog.conn.cursor() as cursor:
            try:
                # Unselect the previously selected character
                cursor.execute(
                    """UPDATE "character"
                    SET selected_character = False
                    WHERE player_id = %s AND server_id = %s""",
                    (player_id, server_id)
                )

                # Select the new character
                cursor.execute(
                    """UPDATE "character"
                    SET selected_character = True
                    WHERE character_id = %s AND server_id = %s""",
                    (character_id, server_id)
                )
            except Exception as e:
                self.cog.conn.rollback()
                print(e)
                return False

            self.cog.conn.commit()
            return True



class CharacterSelectButton(ui.Button):
    """Button to fetch and display existing characters"""

    def __init__(self, ctx: commands.Context, cog: CharacterCreation):
        super().__init__(style=discord.ButtonStyle.blurple, label="Select Character")
        self.ctx = ctx
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        """Handles displaying a list of characters for selection"""
        await interaction.response.defer()

        result = self.get_characters()

        if not result:
            await interaction.followup.send(
                "You don't have any characters yet. Please create one first!", ephemeral=True
            )
            return
        embeds = []
        views = []

        for character in result:
            embed = discord.Embed(
                title=character["character_name"],
                description=f"{character['race_name']} {character['class_name']}",
                color=discord.Color.green()
            )
            embed.add_field(name="Health", value=character["health"])
            embed.add_field(name="Mana", value=character["mana"])
            embed.add_field(name="Craft Skill",
                            value=character["craft_skill"])
            embed.add_field(name="Experience",
                            value=character["experience"])

            image_url = character.get("image_url")
            if image_url:
                embed.set_image(url=image_url)

            view = ui.View()
            view.add_item(CharacterSelectButtonItem(
                ctx=self.ctx,
                cog=self.cog,
                character_name=character["character_name"],
                character_id=character["character_id"]
            ))

            embeds.append(embed)
            views.append(view)

        # Send the embeds with the buttons
        for embed, view in zip(embeds, views):
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            
    def get_characters(self) -> list[dict]:
        """gets the character of a player"""
        query = """
            SELECT character_id, character_name, race_name, class_name, health, mana, craft_skill, experience, image_url
            FROM "character"
            JOIN race ON "character".race_id = race.race_id
            JOIN class ON "character".class_id = class.class_id
            WHERE "character".player_id = (SELECT player_id FROM player WHERE player_name = %s) 
            AND "character".server_id = %s;
        """
        with self.cog.conn.cursor() as cursor:
            cursor.execute(
                query, (self.ctx.author.name, self.ctx.guild.id))
            result = cursor.fetchall()
            return result


class RaceSelect(ui.View):
    """The View that shows all the races"""

    def __init__(self, cog: CharacterCreation, ctx: commands.Context, message: str, races: dict[int, str], classes: dict[int, str], timeout: int = 180):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.ctx = ctx
        self.message = message
        self.races = races
        self.classes = classes

        for race_id, race_name in races.items():
            self.add_item(RaceButton(
                ctx, race_id, race_name, classes, self.cog))


class RaceButton(ui.Button):
    """A button to select the characters race"""
    def __init__(self, ctx: commands.Context, race_id: int, race_name: str, classes: dict[int, str], cog: CharacterCreation):
        super().__init__(style=discord.ButtonStyle.grey, label=race_name)
        self.ctx = ctx
        self.race_id = race_id
        self.classes = classes
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = ClassSelect(self.ctx, self.race_id, self.classes, self.cog)
        await interaction.followup.send("Choose your Class:", view=view, ephemeral=True)


class ClassSelect(ui.View):
    """Creates a view for the different classes the character can be"""

    def __init__(self, ctx: commands.Context, race_id: int, classes: dict[int, str], cog: CharacterCreation, timeout=180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.race_id = race_id
        self.classes = classes
        self.cog = cog

        for class_id, class_name in classes.items():
            self.add_item(ClassButton(
                ctx, race_id, class_id, class_name, self.cog))


class ClassButton(ui.Button):
    """Creates a button for each class"""

    def __init__(self, ctx: commands.Context, race_id: int, class_id: int, class_name: str, cog: CharacterCreation):
        super().__init__(style=discord.ButtonStyle.grey, label=class_name)
        self.ctx = ctx
        self.race_id = race_id
        self.class_id = class_id
        self.class_name = class_name
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        """Handles class selection and character creation"""
        await interaction.response.defer()

        # Get the player_id from the player table
        player_name = self.ctx.author.name
        character_name = self.cog.character_name
        race_id = self.race_id
        class_id = self.class_id

        # Fetch player_id based on the player's name
        query = """
        SELECT player_id FROM player WHERE player_name = %s
        """
        with self.cog.conn.cursor() as cursor:
            cursor.execute(query, (player_name,))
            player_result = cursor.fetchone()
            if player_result:
                player_id = player_result['player_id']
            else:
                cursor.execute(
                    "INSERT INTO player (player_name, server_id) VALUES (%s, %s) RETURNING player_id",
                    (self.ctx.author.name, self.ctx.guild.id)
                )
                player_id = cursor.fetchone()["player_id"]
                self.cog.conn.commit()

        # Database insert logic
        self.create_character_in_db(
            player_id, character_name, race_id, class_id)

        # Send confirmation message
        await interaction.followup.send(f"Character {character_name} created as a {self.cog.races[race_id]} {self.class_name}!", ephemeral=False)

    def create_character_in_db(self, player_id: int, character_name: str, race_id: int, class_id: int):
        """Create the character in the database using player_id, race_id, and class_id"""
        query = """
            INSERT INTO "character" (character_name, race_id, class_id, player_id, server_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        with self.cog.conn.cursor() as cursor:
            cursor.execute(
                query, (character_name, race_id, class_id, player_id, self.ctx.guild.id))
            self.cog.conn.commit()


async def setup(bot: commands.Bot):
    """Sets up the character creation cog with a database connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(CharacterCreation(bot, conn))
