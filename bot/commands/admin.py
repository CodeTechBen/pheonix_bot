

import discord
from discord.ext import commands
import discord.ext.commands
from psycopg2.extensions import connection

import discord.ext


class Admin(commands.Cog):
    """Commands for managing player characters"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn

    @commands.command()
    async def add_server(self, ctx: discord.ext.commands.context):
        """Manually uploads the server to the DB"""
        await ctx.send(upload_server(ctx.guild, self.conn))
