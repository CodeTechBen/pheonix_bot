# Yssadrig Eternal RP - Discord Bot

## Introduction
This is a open source project to create a discord bot for Yssadrig Eternal RP server. This will handle the tasks that admins had to do manually as well as be a RP tool for users.

# Features
This will be a all in one bot that will handle;
- Currency
- Stores
- Magic
- Races
- Classes
- Locations
- Weather

# Prerequisites
- install `python`
- create a `.venv` using ```python3 -m venv .venv``` in the terminal
## Database
- install the requirements using ```pip install -r requirements.txt```
- create a psql database (if running locally) using ```psql -U <username> -d postgres``` then in the terminal type ```CREATE DATABASE <DB_NAME>```, Put this information in the `.env`.
- Next make the schema using ```bash reset.sh```
## Discord BOT
- get the secret token for your discord bot from developer [portal](https://discord.com/developers/applications/)
- In your `.env` put `DISCORD_TOKEN=` and then put your secret token.

# Collaborators

[CodeTechBen](https://github.com/CodeTechBen)