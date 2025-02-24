"""Main file for discord bot"""
from os import environ as ENV
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

def get_connection() -> connection:
    """Returns a postgres connection"""
    print("Connecting to database...")
    conn = psycopg2.connect(
        dbname=ENV['DB_NAME'],
        user=ENV['DB_USER'],
        host=ENV['DB_HOST'],
        port=ENV['DB_PORT'],
        cursor_factory=RealDictCursor)
    print("Connected to database.")
    return conn

if __name__ == "__main__":
    load_dotenv()
