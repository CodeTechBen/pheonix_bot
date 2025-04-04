import discord
from discord.ext import commands
import asyncio

# Load bot token from config
from config import TOKEN, COMMAND_PREFIX

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX,
                   intents=intents)

# Load cogs dynamically
async def load_cogs():
    await bot.load_extension("bot.commands.admin")
    await bot.load_extension("bot.commands.character")
    await bot.load_extension("bot.commands.creature")
    await bot.load_extension("bot.commands.location")
    await bot.load_extension("bot.commands.new_spell")
    await bot.load_extension("bot.commands.create_character")
    await bot.load_extension("bot.combat_test.combat")
    print('Loaded all cogs')


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print("\nLoaded commands:")
    for command in bot.commands:
        print(command.name)

# Run bot


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":

    asyncio.run(main())
