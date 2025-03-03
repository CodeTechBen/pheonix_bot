from os import environ as ENV
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Bot Token
TOKEN = ENV["DISCORD_TOKEN"]

# Bot command prefix
COMMAND_PREFIX = "!"
