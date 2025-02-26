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
- Seed the database using ```bash seed.sh```

## Discord BOT
- get the secret token for your discord bot from developer [portal](https://discord.com/developers/applications/)
- In your `.env` put `DISCORD_TOKEN=` and then put your secret token.
- If your running this bot locally on your machine you can simply use the command ```python3 main.py``` now.

## Using this bot in your server?
- Check that the bot added your server to the database, if in doubt use ```!add_server``` in any channel.
- Add locations to the database.
    - This bot expects that the server will have regions as forums and locations are threads so to use this functionality shape your Discord like that.
    - Go into a thread that is named after a settlement and run the command ```!create_settlement```
- Create classes by using ```!create_class  <class_name> <is_playable>``` e.g. ```!create_class wizard True``` or ```!create_class Enemy False```
- Create races by using ```"Usage: !create_race <class_race> <is_playable> <speed? default = 30>``` e.g. ```!create_race Dwarf True 25``` or ```!create_race Robot False```


# Collaborators

[CodeTechBen](https://github.com/CodeTechBen)
