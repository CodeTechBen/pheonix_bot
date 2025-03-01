"""commands that refer to spells
- !create_spell: Lets an Admin create a spell
"""

import discord
from discord.ext import commands
from psycopg2.extensions import connection


class Spell(commands.Cog):

    def __init__(self, bot: commands.bot.Bot, conn: connection):
        self.bot = bot
        self.conn = conn

    @commands.command()
    async def create_spell(self, ctx: discord.ext.commands.context):
        """Command to generate a spell"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send('You must be an admin to use this command.')
            return

        spell_name = await get_input(ctx, self.bot, "📝 Enter the spell name:")
        if not spell_name:
            return

        spell_description = await get_input(ctx, self.bot, "📖 Enter spell description:")
        if not spell_description:
            return

        spell_power = await get_input(ctx, self.bot, "💥 Enter spell power (1-100):", int)
        if spell_power is None:
            return

        mana_cost = await get_input(ctx, self.bot, "🔋 Enter mana cost:", int)
        if mana_cost is None:
            return

        cooldown = await get_input(ctx, self.bot, "⏳ Enter cooldown (in turns):", int, True)
        if cooldown is None:
            return

        scaling_factor = await get_input(ctx, self.bot, "🎚️ Enter scaling factor (0.1 - 2.0):", float)
        if scaling_factor is None:
            return

        # Fetch spell types
        spell_types = get_spell_type_map(self.conn)
        if not spell_types:
            await ctx.send("❌ No spell types found in the database.")
            return

        await ctx.send(embed=create_embed(
            "📜 Spell Types", "Available spell types:", spell_types, discord.Color.blue()))
        spell_type_id = await get_input(ctx, self.bot, "⚡ Enter the **ID** of the spell type:", int)
        if spell_type_id is None or spell_type_id not in spell_types:
            await ctx.send("❌ Invalid spell type ID. Try again.")
            return

        # Fetch Elements
        element_map = get_element_map(self.conn)
        await ctx.send(embed=create_embed(
            "🔥 Elements", "Available Elements", element_map, discord.Color.red()))
        element_id = await get_input(ctx, self.bot, "🔥 Enter the **ID** of the element:", int)

        # Fetch available classes
        classes = get_class_map(self.conn, ctx.guild.id)
        await ctx.send(embed=create_embed(
            "🛡️ Classes", "Available classes:", classes, discord.Color.green()))
        class_id = await get_input(
            ctx, bot, "⚔️ Enter the **ID** of the class (or `0` if none):", int, True)
        class_id = None if class_id == 0 else class_id

        # Fetch available races
        races = get_race_map(self.conn, ctx.guild.id)
        await ctx.send(embed=create_embed(
            "🧬 Races", "Available races:", races, discord.Color.purple()))
        race_id = await get_input(
            ctx, bot, "🧬 Enter the **ID** of the race (or `0` if none):", int, True)
        race_id = None if race_id == 0 else race_id

        # Fetch spell statuses
        spell_statuses = get_spell_status_map(self.conn)
        await ctx.send(embed=create_embed("🌀 Spell Status Effects",
                                          "Available status effects:",
                                          spell_statuses,
                                          discord.Color.purple()))
        spell_status_id = await get_input(
            ctx, self.bot, "🌀 Enter the **ID** of the spell status effect:", int, True)
        spell_status_chance = await get_input(ctx, self.bot, r"% chance of status condition!", int)
        spell_duration = await get_input(ctx, self.bot, "Duration of status condition (in turns)", int)

        # Generate the spell
        response = generate_spell(
            self.conn, ctx.guild.id, spell_name, spell_description, spell_power,
            mana_cost, cooldown, scaling_factor, spell_type_id, element_id,
            spell_status_id, spell_status_chance, spell_duration, class_id, race_id
        )
        await ctx.send(response)

    async def setup(bot):
        """Sets up connection"""
        conn = bot.get_cog("Database").conn
        await bot.add_cog(Spell(bot, conn))
