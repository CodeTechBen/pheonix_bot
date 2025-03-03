"""Defines the creature commands

- !create_race
- !create_class
"""

import discord
from discord.ext import commands
import discord.ext.commands
from psycopg2.extensions import connection

import discord.ext

from bot.database_utils.connection import DatabaseConnection
from bot.database_utils.generate_queries import DataInserter

class Creature(commands.Cog):
    """Commands for managing player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print('Creature cog loaded')

    @commands.command()
    async def create_class(self,
                           ctx: discord.ext.commands.context,
                           class_name: str = None,
                           is_playable: bool = None):
        """Creates a class in the database"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return

        if not self.is_valid_class(class_name, is_playable):
            await ctx.send("Usage: !create_class <class_name> <True/False>")
            return

        response = DataInserter.generate_class(
            ctx.guild, class_name.title(), is_playable, self.conn)
        await ctx.send(response)

    @commands.command()
    async def create_race(self,
                          ctx: discord.ext.commands.context,
                          race_name: str = None,
                          is_playable: bool = None,
                          speed: int = 30):
        """Creates a race in the database"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return

        if not self.is_valid_class(race_name, is_playable):
            await ctx.send("Usage: !create_race <class_name> <True/False> <speed?>")
            return

        if not isinstance(speed, int):
            return

        response = DataInserter.generate_race(
            ctx.guild, race_name.title(), is_playable, speed, self.conn)
        await ctx.send(response)
    
    def is_valid_class(self, class_name: str, is_playable: bool) -> bool:
        """
        Checks that the class name and is_playable
        is valid before adding to the database."""
        if class_name is None or is_playable is None:
            return False
        if not isinstance(class_name, str):
            return False

        if not isinstance(is_playable, bool):
            return False

        if len(class_name) <= 2 or len(class_name) > 29:
            return False
        return True


async def setup(bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Creature(bot, conn))
