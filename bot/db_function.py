"""Defines the functions that effect the database"""
from os import environ as ENV
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
import discord


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


def upload_server(guild: discord.Guild, conn: connection):
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


def close_connection(conn: connection):
    """Close the database connection"""
    if conn:
        conn.close()
        print("Database connection closed.")
