"""Defines the functions that effect the database"""
from os import environ as ENV
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
import discord
import discord.ext
import discord.ext.commands


def get_connection() -> connection:
    """Returns a single postgres connection"""
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname=ENV['DB_NAME'],
        user=ENV['DB_USER'],
        host=ENV['DB_HOST'],
        port=ENV['DB_PORT'],
        cursor_factory=RealDictCursor)
    print("Connected to database.")
    return conn


def upload_server(guild: discord.Guild, conn: connection) -> str:
    """
    Handles the server join event
    and uploads the server information to the database if not already present"""
    print(f"New server joined: {guild.name} (ID: {guild.id})")

    with conn.cursor() as cursor:
        # Check if the guild_id is already in the discord_server table
        cursor.execute(
            "SELECT 1 FROM server WHERE server_id = %s", (guild.id,))
        exists = cursor.fetchone()

        if exists:
            return f"Server {guild.name} (ID: {guild.id}) already exists in the database."

        cursor.execute("INSERT INTO server (server_id, server_name) VALUES (%s, %s)",
                        (guild.id, guild.name))
        conn.commit()
        return f"Server {guild.name} (ID: {guild.id}) added to the database."


def generate_class(guild: discord.Guild, class_name: str, is_playable: bool, conn: connection):
    """Creates a class in the Database according to user arguments"""
    print(f"Generating new class: {class_name}")

    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO class (class_name, is_playable, server_id) VALUES (%s, %s, %s)",
                        (class_name, is_playable, guild.id)
        )
        conn.commit()
        return f"Class ({class_name}) has been added to the database."


def generate_race(guild: discord.Guild,
                  race_name: str,
                  is_playable: bool,
                  speed: int,
                  conn: connection):
    """Creates a race in the Database according to user arguments"""
    print(f"Generating new race: {race_name}")

    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO race (race_name, speed, is_playable, server_id) VALUES (%s, %s, %s, %s)",
            (race_name, speed, is_playable, guild.id)
        )
        conn.commit()
        return f"Race ({race_name}) has been added to the database."


def get_player_mapping(conn: connection, server_id: int) -> dict[str, int]:
    """Returns a dictionary of player names and their DB ID number for a specific server"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT player_name, player_id FROM player WHERE server_id = %s", (
                server_id,)
        )
        return {row["player_name"]: row["player_id"] for row in cursor.fetchall()}


def create_player(ctx, conn: connection) -> int:
    """Creates a player in the database and returns the player ID"""
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO player (player_name, server_id) VALUES (%s, %s) RETURNING player_id",
            (ctx.author.name, ctx.guild.id)
        )
        player_id = cursor.fetchone()["player_id"]
        conn.commit()
    return player_id


def get_location_mapping(conn: connection, server_id: int) -> dict[int, int]:
    """Gets the channel id and the location id in a dictionary"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT channel_id, location_id FROM location WHERE server_id = %s", (server_id,)
        )
        return {row["channel_id"]: row["location_id"] for row in cursor.fetchall()}


def generate_location(ctx, conn: connection):
    """Generates a location based on the channel this command is run in"""
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO location (location_name, channel_id, server_id)
            VALUES (%s, %s, %s)""", (
                ctx.channel.parent.name, ctx.channel.parent.id, ctx.guild.id
                )
        )
        conn.commit()
        return f'location {ctx.channel.parent.name} added to the database'


def get_settlement_mapping(conn: connection, server_id: int) -> dict:
    """Gets the thread id and settlement id in a dictionary"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT thread_id, settlement_id FROM settlements WHERE server_id = %s", (
                server_id,)
        )
        return {row["thread_id"]: row["settlement_id"] for row in cursor.fetchall()}


def generate_settlement(ctx, conn: connection, location_map: dict[int,int]):
    """Generates a settlement based on the thread id this command is run in."""
    location_id = location_map[ctx.channel.parent.id]
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO settlements (settlement_name, thread_id, location_id, server_id)
            VALUES (%s, %s, %s, %s)""", (
                ctx.channel.name, ctx.channel.id, location_id, ctx.guild.id
            )
        )
        conn.commit()
        return f'settlement {ctx.channel.name} added to database'


def get_character_mapping(conn: connection, player_id: int) -> dict[int, int]:
    """Gets a dictionary for {character_name : character_id} for a specific player"""
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT character_name, character_id
            FROM character
            WHERE player_id = %s""", (player_id,)
        )
        return {row['character_name']: row['character_id'] for row in cursor.fetchall()}


def get_race_map(conn: connection, server_id: int) -> dict[str: int]:
    """Gets a dictionary of {race_name: race_id}"""
    with conn.cursor() as cursor:
        cursor.execute("""SELECT race_name, race_id
                       FROM race
                       WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
        )
        return {row['race_name']: row['race_id'] for row in cursor.fetchall()}


def get_class_map(conn: connection, server_id: int) -> dict[str: int]:
    """Gets a dictionary of {race_name: race_id}"""
    with conn.cursor() as cursor:
        cursor.execute("""SELECT class_name, class_id
                       FROM class
                       WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
                       )
        return {row['class_name']: row['class_id'] for row in cursor.fetchall()}


def get_element_map(conn: connection) -> dict[str: int]:
    """gets a dictionary of {element_name: element_id}"""
    with conn.cursor() as cursor:
        cursor.execute("""SELECT element_name, element_id
                       FROM element""")
        return {row['element_name']: row['element_id'] for row in cursor.fetchall()}


def get_spell_status_map(conn: connection) -> dict[str: int]:
    """Gets a dictionary of {spell_status_name: spell_status_id}"""
    with conn.cursor() as cursor:
        cursor.execute("""SELECT status_name, spell_status_id
                      FROM spell_status""")
        return {row['status_name']: row['spell_status_id'] for row in cursor.fetchall()}


def get_spell_type_map(conn: connection):
    """Gets a dictionary of spell types {spell_type_id: spell_type_name}"""
    with conn.cursor() as cursor:
        cursor.execute("""SELECT spell_type_id, spell_type_name
                       FROM spell_type""")
        return {row['spell_type_id']: row['spell_type_name'] for row in cursor.fetchall()}


def generate_spell(conn: connection,
                   server_id: int,
                   spell_name: str,
                   spell_description: str,
                   spell_power: int,
                   mana_cost: int,
                   cooldown: int,
                   scaling_factor: float,
                   spell_type_id: int,
                   element_id: int,
                   spell_status_id: int,
                   spell_status_chance: int,
                   spell_duration: int,
                   class_id: int = None,
                   race_id: int = None):
    """Inserts a new spell into the database and assigns its status."""
    try:
        with conn.cursor() as cursor:
            # Insert spell into spells table
            spell_sql = """
            INSERT INTO spells (spell_name, spell_description, spell_power, mana_cost, cooldown, scaling_factor, 
                                spell_type_id, element_id, class_id, race_id, server_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
            RETURNING spell_id;
            """
            spell_values = (spell_name,
                            spell_description,
                            spell_power,
                            mana_cost,
                            cooldown,
                            scaling_factor,
                            spell_type_id,
                            element_id,
                            class_id,
                            race_id,
                            server_id)

            cursor.execute(spell_sql, spell_values)
            spell_id = cursor.fetchone().get('spell_id')

            if spell_id is None:
                conn.rollback()
                return "❌ Error: Spell creation failed. Please try again."

            # Insert into spell_status_spell_assignment table
            status_sql = """
            INSERT INTO spell_status_spell_assignment (spell_id, spell_status_id, chance, duration)
            VALUES (%s, %s, %s, %s);
            """
            status_values = (spell_id, spell_status_id, spell_status_chance, spell_duration)

            cursor.execute(status_sql, status_values)

            # Commit transaction if everything is successful
            conn.commit()

        return f"✨ Spell `{spell_name}` has been created!"

    except Exception as e:
        conn.rollback()
        return f"❌ Error: {str(e)}"



def generate_character(conn: connection,
                       ctx,
                       character_name: str,
                       race_id: int,
                       class_id: int,
                       player_id: int,
                       faction_id=None) -> str:
    """Generates a new character"""

    with conn.cursor() as cursor:
        # Deselect previous character for this player
        cursor.execute(
            """UPDATE character
               SET selected_character = False
               WHERE player_id = %s AND server_id = %s""",
            (player_id, ctx.guild.id)
        )

        # Insert new character with defaults
        cursor.execute(
            """INSERT INTO character (character_name,
                                    race_id,
                                    class_id,
                                    player_id,
                                    faction_id,
                                    server_id)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (character_name, race_id, class_id,
             player_id, faction_id, ctx.guild.id)
        )

        conn.commit()
        return f'{character_name} has been made and selected.'


def close_connection(conn: connection):
    """Close the database connection"""
    if conn:
        conn.close()
        print("Database connection closed.")
