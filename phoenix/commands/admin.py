"""Defines the Admin commands usable by the discord bot.

Admin commands are explicitly for the maintaining of the Database of server."""

from discord.ext import commands
from psycopg2.extensions import connection

# from database_utils import DatabaseConnection, DataInserter
# from phoenix.database_utils import DatabaseConnection, DataInserter
from database_utils.generate_queries import DataInserter
from database_utils.connection import DatabaseConnection


class Admin(commands.Cog):
    """Commands for managing player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print('Admin cog loaded')


    @commands.command()
    async def add_server(self, ctx: commands.Context):
        """Manually uploads the server to the DB"""
        await ctx.send(DataInserter.upload_server(ctx.guild, self.conn))


async def setup(bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Admin(bot, conn))
