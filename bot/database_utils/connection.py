"""Defines the connection to the database"""
from os import environ as ENV
import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

class DatabaseConnection:
    _connection = None

    @classmethod
    def get_connection(cls) -> connection:
        """Returns a single postgres connection"""
        if cls._connection is None:
            cls._connection = psycopg2.connect(
                dbname=ENV['DB_NAME'],
                user=ENV['DB_USER'],
                host=ENV['DB_HOST'],
                port=ENV['DB_PORT'],
                cursor_factory=RealDictCursor)
        return cls._connection  # Return the existing connection

    @classmethod
    def close_connection(cls):
        if cls._connection:
            cls._connection.close()
            cls._connection = None

