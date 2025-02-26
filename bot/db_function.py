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


def close_connection(conn: connection):
    """Close the database connection"""
    if conn:
        conn.close()
        print("Database connection closed.")
