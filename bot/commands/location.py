"""Commands that refer to a location.

- !create_settlement

"""
import discord
from discord.ext import commands
from psycopg2.extensions import connection
from bot.database_utils import (DatabaseMapper,
                                DataInserter,
                                DatabaseConnection)

class Location(commands.Cog):
    """commands that manage a location"""

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        print('Location log loaded')


    def is_valid_settlement(self, ctx: commands.Context) -> tuple[bool, str]:
        """
        Checks if the command location is a valid settlement
        i.e. A thread inside of a forum
        """
        if not isinstance(ctx.channel, discord.Thread):
            return False, "This command must be used inside a forum thread."

        if not isinstance(ctx.channel.parent, discord.ForumChannel):
            return False, "This thread is not part of a forum channel."
        return True, None

    @commands.command()
    async def create_settlement(self, ctx: commands.Context):
        """Sets a channel as a location"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("You must be an admin to use this command.")
            return

        is_valid, message = self.is_valid_settlement(ctx)
        if not is_valid:
            await ctx.send(message)
            return

        await ctx.send(
            f"Forum Channel: **{ctx.channel.parent.name}** (ID: `{ctx.channel.parent.id}`)\n"
            f"Thread: **{ctx.channel.name}** (ID: `{ctx.channel.id}`)"
        )

        location_map = DatabaseMapper.get_location_mapping(self.conn, ctx.guild.id)
        if ctx.channel.parent.id not in location_map.keys():
            # How to get a link to the location
            print(
                f"https://discord.com/channels/{ctx.guild.id}/{ctx.channel.parent.id}")
            await ctx.send(DataInserter.generate_location(ctx, self.conn))
        location_map = DatabaseMapper.get_location_mapping(self.conn, ctx.guild.id)
        settlement_map = DatabaseMapper.get_settlement_mapping(self.conn, ctx.guild.id)
        if ctx.channel.id not in settlement_map.keys():
            await ctx.send(DataInserter.generate_settlement(ctx, self.conn, location_map))


async def setup(bot: commands.bot.Bot):
    """Sets up connection"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Location(bot, conn))
