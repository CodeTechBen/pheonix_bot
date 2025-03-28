"""functions that puts data into the database"""
from datetime import datetime
from random import randint
import discord
from discord.ext import commands
from psycopg2.extensions import connection
import psycopg2
from .fetch_queries import DatabaseIDFetch

class DataInserter:
    """
    This class defines the functions
    that is used to insert data into the database"""

    @classmethod
    def upload_server(cls, guild: discord.Guild, conn: connection) -> str:
        """
        Handles the server join event
        and uploads the server information to the database if not already present"""
        print(f"New server joined: {guild.name} (ID: {guild.id})")
        try:
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
        except Exception as e:
            print(e)

    @classmethod
    def generate_class(cls,
                       guild: discord.Guild,
                       class_name: str,
                       is_playable: bool,
                       conn: connection) -> str:
        """Creates a class in the Database according to user arguments"""
        print(f"Generating new class: {class_name}")

        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO class (class_name, is_playable, server_id) VALUES (%s, %s, %s)",
                (class_name, is_playable, guild.id)
            )
            conn.commit()
            return f"Class ({class_name}) has been added to the database."


    @classmethod
    def generate_race(cls,
                    guild: discord.Guild,
                    race_name: str,
                    is_playable: bool,
                    speed: int,
                    conn: connection) -> str:
        """Creates a race in the Database according to user arguments"""
        print(f"Generating new race: {race_name}")
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO race (race_name, speed, is_playable, server_id)
                    VALUES (%s, %s, %s, %s)""",
                    (race_name, speed, is_playable, guild.id)
                )
                conn.commit()
                return f"Race ({race_name}) has been added to the database."
        except Exception as e:
            print(e)

    @classmethod
    def create_player(cls, ctx, conn: connection) -> int:
        """Creates a player in the database and returns the player ID"""
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO player (player_name, server_id) VALUES (%s, %s) RETURNING player_id",
                (ctx.author.name, ctx.guild.id)
            )
            player_id = cursor.fetchone()["player_id"]
            conn.commit()
        return player_id


    @classmethod
    def generate_location(cls, ctx: commands.Context, conn: connection) -> str:
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


    @classmethod
    def generate_settlement(cls,
                            ctx: commands.Context,
                            conn: connection,
                            location_map: dict[int, int]) -> str:
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


    @classmethod
    def generate_events_for_character(cls, conn: connection, player_name: str):
        """
        Generates all events for the selected character of the given player
        and sets them to the current time.
        
        """
        with conn.cursor() as cursor:
            # Get the character_id of the selected character for the given player
            character_id = DatabaseIDFetch.fetch_selected_character_id(conn, player_name)

            # Retrieve all event_type_id from the event_type table
            cursor.execute("""
                SELECT event_type_id
                FROM "event_type";
                """)
            event_types = cursor.fetchall()

            # Insert an event for each event type with the current timestamp
            for event in event_types:
                event_type_id = event['event_type_id']
                cursor.execute("""
                    INSERT INTO "character_event" (character_id, event_type_id, event_timestamp)
                    VALUES (%s, %s, NOW());
                    """, (character_id, event_type_id))

            conn.commit()

    @classmethod
    def generate_inventory_for_character(cls, conn: connection, player_name: str):
        """generates a inventory for the players selected character"""
        character_id = DatabaseIDFetch.fetch_selected_character_id(conn, player_name)
        with conn.cursor() as cursor:
            query = """INSERT INTO inventory (inventory_name, character_id)
                        VALUES (%s, %s)"""
            cursor.execute(query, ('initial_inventory', character_id))
            conn.commit()


    @classmethod
    def generate_spell(cls,
                       conn: connection,
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
        print('generating spell!!!')
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
                status_values = (spell_id, spell_status_id,
                                spell_status_chance, spell_duration)

                cursor.execute(status_sql, status_values)

                # Commit transaction if everything is successful
                conn.commit()
            print(f"✨ Spell `{spell_name}` has been created!")
            return spell_id

        except Exception as e:
            conn.rollback()
            return f"❌ Error: {str(e)}"


    @classmethod
    def generate_character(cls,
                           conn: connection,
                           ctx: commands.Context,
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


    @classmethod
    def add_spell_to_character(cls,
                               conn: connection,
                               ctx: commands.Context,
                               selected_spell_id: int):
        """Adds a spell to a characters assigned spells"""
        # Add spell to character
        with conn.cursor() as cursor:
            query = """
                        INSERT INTO character_spell_assignment (character_id, spell_id)
                        SELECT character_id, %s
                        FROM character
                        JOIN player ON character.player_id = player.player_id
                        WHERE player.player_name = %s
                        AND character.selected_character = TRUE;
                    """
            cursor.execute(query, (selected_spell_id, ctx.author.name))
            conn.commit()


    @classmethod
    def insert_item_player_inventory(cls,
                                     conn: connection,
                                     item_name: str,
                                     item_value: int,
                                     character_id: int) -> int:
        """Inserts an item into a characters inventory"""
        with conn.cursor() as cursor:
            # Insert item into inventory
            query = """
                    INSERT INTO item (item_name, value, inventory_id)
                    VALUES (%s, %s, (SELECT inventory_id FROM inventory WHERE character_id = %s))
                    RETURNING item_id;
                    """
            cursor.execute(query, (item_name, item_value, character_id))
            conn.commit()

            return cursor.fetchone().get('item_id')


    @classmethod
    def update_last_event(cls,
                          conn: connection,
                          player_name: str,
                          event_name: str,
                          timestamp: datetime):
        """Inserts a new event for the selected character"""
        with conn.cursor() as cursor:
            # Get the character_id for the selected character
            cursor.execute("""
                SELECT c.character_id
                FROM "character" c
                JOIN "player" p ON c.player_id = p.player_id
                WHERE p.player_name = %s
                AND c.selected_character = TRUE;
                """, (player_name,))
            character_id = cursor.fetchone()['character_id']

            # Get the event_type_id for the given event_name
            cursor.execute("""
                SELECT event_type_id
                FROM "event_type"
                WHERE event_name = %s;
                """, (event_name,))
            event_type_id = cursor.fetchone()['event_type_id']

            # Insert the new event
            cursor.execute("""
                INSERT INTO "character_event" (character_id, event_type_id, event_timestamp)
                VALUES (%s, %s, %s);
                """, (character_id, event_type_id, timestamp))

            conn.commit()


    @classmethod
    def increase_wallet(cls, conn: connection, player_name: str, profit: int) -> str:
        """Increases the amount in the selected character's wallet"""
        with conn.cursor() as cursor:
            query = """
                    WITH selected_character AS (
                        SELECT c.character_id
                        FROM "character" c
                        JOIN player p ON c.player_id = p.player_id
                        WHERE p.player_name = %s
                        AND c.selected_character = TRUE
                    )
                    UPDATE "character"
                    SET shards = shards + %s
                    WHERE character_id IN (SELECT character_id FROM selected_character)
                    RETURNING shards;
                    """
            cursor.execute(query, (player_name, profit))
            new_shards = cursor.fetchone().get('shards')

            if new_shards:
                conn.commit()
                return f"""{player_name.title()} has received **{profit}** shards!
    You now have **{new_shards}** in your wallet."""
            return f"No selected character found for {player_name}."


    @classmethod
    def add_character_image(cls, conn, player_name: str, image_url: str) -> str:
        """Adds a character image to the selected player character"""

        query_select = """
                SELECT c.character_id
                FROM "character" c
                JOIN player p ON c.player_id = p.player_id
                WHERE p.player_name = %s
                AND c.selected_character = TRUE
        """

        query_update = """
            UPDATE "character"
            SET image_url = %s
            WHERE character_id = %s;
        """

        try:
            with conn.cursor() as cursor:
                # Get the character_id of the selected character
                cursor.execute(query_select, (player_name,))
                result = cursor.fetchone()

                if result is None:
                    return f"No selected character found for player '{player_name}'."

                character_id = result.get('character_id')

                # Update the character's image URL
                cursor.execute(query_update, (image_url, character_id))
                conn.commit()

                return f"Successfully updated image for {player_name}'s character."

        except psycopg2.Error as e:
            conn.rollback()
            return f"Database error: {str(e)}"
    

    @classmethod
    def select_new_character(self, conn: connection, player_id, server_id, character_id):
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """UPDATE character
                    SET selected_character = False
                    WHERE player_id = %s AND server_id = %s""",
                    (player_id, server_id)
                )

                cursor.execute(
                    """UPDATE character
                    SET selected_character = True
                    WHERE character_id = %s AND server_id = %s""",
                    (character_id, server_id)
                )
            except Exception as e:
                conn.rollback()
                print(e)
                return False
            
            conn.commit()
            return True


    @classmethod
    def enchant_item(cls, conn: connection, item_id: int, charges: int, spell_id: int) -> bool:
        """Allows a user to enchant an item with a spell."""
        try:
            with conn.cursor() as cursor:
                enchant_query = """UPDATE item
                                SET spell_id = %s,
                                    spell_charges = %s
                                WHERE item_id = %s"""
                cursor.execute(enchant_query, (spell_id, charges, item_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error enchanting item: {e}")
            conn.rollback()
            return False
