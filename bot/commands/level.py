"""Defines the Level up command usable by the discord bot."""
import math
import discord
from discord.ext import commands
from psycopg2.extensions import connection

from bot.database_utils import DatabaseConnection


def xp_required_for_level(level: int) -> int:
    """Exponential XP requirement. Level 2 needs 400 XP."""
    return int(400 * math.pow(1.5, level - 1))


class LevelUp(commands.Cog):
    """Commands for leveling up player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print('Level cog loaded')


    @commands.command()
    async def level(self, ctx: commands.Context):
        """Checks if the player can level up"""
        xp_data = self.get_player_xp(ctx, self.conn)
        level = xp_data.get('level')
        current_xp = xp_data.get('experience')
        try:
            xp_requirement = xp_required_for_level(level)
            if current_xp >= xp_requirement:
                self.level_up_player(ctx.author.name, level + 1)
                await ctx.send(f"🎉 You leveled up to level {level + 1}!")

                view = StatUpgradeView(self.conn, ctx.author.name)
                await ctx.send("Choose a stat to upgrade:", view=view)
            else:
                await ctx.send(f"You need {xp_requirement - current_xp} more XP to level up.")
        except Exception as e:
            print(e)

    def get_player_xp(self, ctx: commands.Context, conn: connection) -> dict[str: int]:
        """Gets the players current XP"""
        query = """SELECT c.experience, c.level
                    FROM character AS c
                    WHERE c.character_id = (
                        SELECT c.character_id
                        FROM "character" c
                        JOIN player p ON c.player_id = p.player_id
                        WHERE p.player_name = %s
                        AND c.selected_character = TRUE
                    );"""

        with conn.cursor() as cursor:
            cursor.execute(query, (ctx.author.name,))
            return cursor.fetchone()

    def level_up_player(self, player_name: str, new_level: int):
        query = """
        UPDATE character
        SET level = %s
        WHERE character_id = (
            SELECT c.character_id
            FROM character c
            JOIN player p ON c.player_id = p.player_id
            WHERE p.player_name = %s AND c.selected_character = TRUE
        );
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (new_level, player_name))
            self.conn.commit()

class StatUpgradeView(discord.ui.View):
    def __init__(self, conn: connection, player_name: str):
        super().__init__(timeout=30)
        self.conn = conn
        self.player_name = player_name

    async def upgrade_health_stat(self, interaction: discord.Interaction):
        query = """
        UPDATE character
        SET health = health + 50
        WHERE character_id = (
            SELECT c.character_id
            FROM character c
            JOIN player p ON c.player_id = p.player_id
            WHERE p.player_name = %s AND c.selected_character = TRUE
        )
        RETURNING health;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.player_name,))
            new_health = cursor.fetchone().get('health')
            self.conn.commit()

        await interaction.response.send_message(f"✅ Health increased!, new health = {new_health}", ephemeral=True)


    async def upgrade_mana_stat(self, interaction: discord.Interaction):
        query = f"""
        UPDATE character
        SET mana = mana + 50
        WHERE character_id = (
            SELECT c.character_id
            FROM character c
            JOIN player p ON c.player_id = p.player_id
            WHERE p.player_name = %s AND c.selected_character = TRUE
        )        
        RETURNING mana;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.player_name,))
            new_mana = cursor.fetchone().get('mana')
            self.conn.commit()

        await interaction.response.send_message(f"✅ Mana increased!, new mana = {new_mana}", ephemeral=True)


    async def upgrade_craft_stat(self, interaction: discord.Interaction):
        query = f"""
        UPDATE character
        SET craft_skill = craft_skill + 10
        WHERE character_id = (
            SELECT c.character_id
            FROM character c
            JOIN player p ON c.player_id = p.player_id
            WHERE p.player_name = %s AND c.selected_character = TRUE
        )
        RETURNING craft_skill;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (self.player_name,))
            new_craft_skill = cursor.fetchone().get('craft_skill')
            self.conn.commit()

        await interaction.response.send_message(f"✅ craft skill increased!, new craft skill = {new_craft_skill}", ephemeral=True)


    @discord.ui.button(label="Health", style=discord.ButtonStyle.red)
    async def health_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.upgrade_health_stat(interaction)

    @discord.ui.button(label="Mana", style=discord.ButtonStyle.blurple)
    async def mana_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.upgrade_mana_stat(interaction)

    @discord.ui.button(label="Craft Skill", style=discord.ButtonStyle.gray)
    async def craft_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.upgrade_craft_stat(interaction)

async def setup(bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(LevelUp(bot, conn))
