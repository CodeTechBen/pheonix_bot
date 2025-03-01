"""functions that gets the primary keys of tables from the database"""

import discord
from datetime import datetime
from psycopg2.extensions import connection


class DatabaseMapper:
    """This defines the functions that get the mappings from the database"""

    @classmethod
    def get_player_mapping(conn: connection, server_id: int) -> dict[str, int]:
        """Returns a dictionary of player names and their DB ID number for a specific server"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT player_name, player_id FROM player WHERE server_id = %s", (
                    server_id,)
            )
            return {row["player_name"]: row["player_id"] for row in cursor.fetchall()}


    @classmethod
    def get_location_mapping(conn: connection, server_id: int) -> dict[int, int]:
        """Gets the channel id and the location id in a dictionary"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT channel_id, location_id FROM location WHERE server_id = %s", (
                    server_id,)
            )
            return {row["channel_id"]: row["location_id"] for row in cursor.fetchall()}


    @classmethod
    def get_settlement_mapping(conn: connection, server_id: int) -> dict:
        """Gets the thread id and settlement id in a dictionary"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT thread_id, settlement_id FROM settlements WHERE server_id = %s", (
                    server_id,)
            )
            return {row["thread_id"]: row["settlement_id"] for row in cursor.fetchall()}


    @classmethod
    def get_character_mapping(conn: connection, player_id: int) -> dict[int, int]:
        """Gets a dictionary for {character_name : character_id} for a specific player"""
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT character_name, character_id
                FROM character
                WHERE player_id = %s""", (player_id,)
            )
            return {row['character_name']: row['character_id'] for row in cursor.fetchall()}


    @classmethod
    def get_race_map(conn: connection, server_id: int) -> dict[str: int]:
        """Gets a dictionary of {race_name: race_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT race_name, race_id
                        FROM race
                        WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
                        )
            return {row['race_name']: row['race_id'] for row in cursor.fetchall()}


    @classmethod
    def get_class_map(conn: connection, server_id: int) -> dict[str: int]:
        """Gets a dictionary of {race_name: race_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT class_name, class_id
                        FROM class
                        WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
                        )
            return {row['class_name']: row['class_id'] for row in cursor.fetchall()}


    @classmethod
    def get_element_map(conn: connection) -> dict[str: int]:
        """gets a dictionary of {element_name: element_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT element_name, element_id
                        FROM element""")
            return {row['element_name']: row['element_id'] for row in cursor.fetchall()}


    @classmethod
    def get_spell_status_map(conn: connection) -> dict[str: int]:
        """Gets a dictionary of {spell_status_name: spell_status_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT status_name, spell_status_id
                        FROM spell_status""")
            return {row['status_name']: row['spell_status_id'] for row in cursor.fetchall()}


    @classmethod
    def get_spell_type_map(conn: connection):
        """Gets a dictionary of spell types {spell_type_id: spell_type_name}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT spell_type_id, spell_type_name
                        FROM spell_type""")
            return {row['spell_type_id']: row['spell_type_name'] for row in cursor.fetchall()}


    @classmethod
    def get_last_event(conn: connection, player_name: str, event_name: str) -> datetime:
        """Gets the last time the selected character performed a specific event"""
        with conn.cursor() as cursor:
            query = """
                    SELECT c.character_name, ce.event_timestamp, et.event_name
                    FROM character_event AS ce
                    JOIN event_type AS et ON ce.event_type_id = et.event_type_id
                    JOIN character AS c ON ce.character_id = c.character_id
                    JOIN player AS p ON c.player_id = p.player_id
                    WHERE c.character_id = (
                        SELECT c.character_id
                        FROM "character" c
                        JOIN player p ON c.player_id = p.player_id
                        WHERE p.player_name = %s
                        AND c.selected_character = TRUE
                    )
                    AND et.event_name = %s
                    ORDER BY ce.event_timestamp DESC
                    LIMIT 1;
                    """
            cursor.execute(query, (player_name, event_name))
            result = cursor.fetchone()
            print(result)
            return result['event_timestamp'] if result else None


    @classmethod
    def get_craft_skill(conn: connection, player_name) -> dict[str: int]:
        """Gets a character id and their craft skill"""
        with conn.cursor() as cursor:
            # Get the player's selected character's craft skill
            query = """
                    SELECT c.character_id, c.craft_skill
                    FROM "character" c
                    JOIN player p ON c.player_id = p.player_id
                    WHERE p.player_name = %s
                    AND c.selected_character = TRUE;
                    """
            cursor.execute(query, (player_name,))
            result = cursor.fetchone()

            if not result:
                return f"{player_name}, you need to select a character first!"
            return result


    @classmethod
    def get_equipped_spells(conn: connection, ctx) -> list[dict]:
        """Checks the last equipped spells"""
        query = """
                SELECT 
                    s.spell_id,
                    s.spell_name,
                    s.spell_description,
                    s.spell_power,
                    s.mana_cost,
                    s.cooldown,
                    e.element_name,
                    ss.status_name,
                    sa.chance,
                    sa.duration
                FROM character c
                JOIN player p ON c.player_id = p.player_id
                JOIN character_spell_assignment csa ON c.character_id = csa.character_id
                JOIN spells s ON csa.spell_id = s.spell_id
                JOIN element e ON s.element_id = e.element_id
                LEFT JOIN spell_status_spell_assignment sa ON s.spell_id = sa.spell_id
                LEFT JOIN spell_status ss ON sa.spell_status_id = ss.spell_status_id
                WHERE p.player_name = %s
                AND c.selected_character = TRUE
                ORDER BY sa.spell_status_spell_assignment_id DESC
                LIMIT 4;
                """
        with conn.cursor() as cursor:
            cursor.execute(query, (ctx.author.name,))
            return cursor.fetchall()


    @classmethod
    def get_potential_player_spells(conn: connection, ctx) -> list[dict]:
        """Returns a dictionary of player spells"""
        with conn.cursor() as cursor:
            query = """
                WITH selected_character AS (
                    SELECT c.character_id, c.race_id, c.class_id
                    FROM character c
                    JOIN player p ON c.player_id = p.player_id
                    WHERE p.player_name = %s
                    AND c.selected_character = TRUE
                )
                SELECT
                    s.spell_id,
                    s.spell_name,
                    s.spell_description,
                    s.spell_power,
                    s.mana_cost,
                    s.cooldown,
                    e.element_name,
                    ss.status_name,
                    sssa.chance,
                    sssa.duration
                FROM spells s
                JOIN selected_character sc
                    ON s.race_id = sc.race_id OR s.class_id = sc.class_id
                JOIN element e ON s.element_id = e.element_id
                LEFT JOIN spell_status_spell_assignment sssa ON s.spell_id = sssa.spell_id
                LEFT JOIN spell_status ss ON sssa.spell_status_id = ss.spell_status_id
                ORDER BY s.spell_id;

            """
            cursor.execute(query, (ctx.author.name,))
            return cursor.fetchall()
        

class DatabaseIDFetch:
    """This defines the functions used to get the ID of a table in the database"""

    @classmethod
    def fetch_selected_character_id(conn: connection, player_name: str):
        """Gets the selected character id for a specific player name"""
        with conn.cursor() as cursor:
            # Get the character_id of the selected character for the given player
            cursor.execute("""
                SELECT c.character_id
                FROM "character" c
                JOIN "player" p ON c.player_id = p.player_id
                WHERE p.player_name = %s
                AND c.selected_character = TRUE;
                """, (player_name,))
            result = cursor.fetchone()

            if not result:
                raise ValueError(
                    f"No selected character found for player: {player_name}")

            character_id = result['character_id']
            return character_id
    

    @classmethod
    def get_player_id(conn: connection, player_name: str, server_id: int):
        """Fetches the player_id based on player_name and server_id."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT player_id 
                FROM player 
                WHERE player_name = %s AND server_id = %s
            """, (player_name, server_id))
            player = cursor.fetchone()
            return player.get('player_id') if player else None
    
    @classmethod
    def get_selected_character_id(conn, player_id: int):
        """Fetches the character_id for the selected character."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT character_id 
                FROM character 
                WHERE player_id = %s AND selected_character = TRUE
            """, (player_id,))
            character = cursor.fetchone()
            return character.get('character_id') if character else None
        
    @classmethod
    def get_inventory_id(conn, character_id: int):
        """Fetches the inventory_id for the character."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT inventory_id 
                FROM inventory 
                WHERE character_id = %s
            """, (character_id,))
            inventory = cursor.fetchone()
            return inventory.get('inventory_id') if inventory else None


class InventoryDatabase:
    """Handles inventory-related database operations"""

    @classmethod
    def get_items_in_inventory(cls, conn: connection, inventory_id: int):
        """Fetches all items in the specified inventory."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT item_id, item_name, value 
                FROM item 
                WHERE inventory_id = %s
            """, (inventory_id,))
            return cursor.fetchall()


class EmbedHelper:
    """Handles creating embeds for displaying data in Discord"""

    @classmethod
    def create_map_embed(cls, title, description, data_dict, color):
        """Creates an embed message for Discord with selectable options."""
        embed = discord.Embed(
            title=title, description=description, color=color)
        for name, _id in data_dict.items():
            embed.add_field(name=f"🔹 {name}",
                            value=f"ID: `{_id}`", inline=False)
        return embed

    @classmethod
    def create_inventory_embed(cls, ctx, items):
        """Creates an embed to display the inventory items."""
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Inventory",
            description="Here are the items in your inventory:",
            color=discord.Color.blue()
        )

        for item in items:
            embed.add_field(
                name=f"{item.get('item_name').title().replace('_', ' ')}",
                value=f"Value: {item.get('value')} {'shard' if item.get('value') == 1 else 'shards'}",
                inline=False
            )
            embed.add_field(name="ID:", value=item.get("item_id"))
        return embed


class UserInputHelper:
    """Handles user input prompts and conversions"""

    @classmethod
    async def get_input(cls, ctx, bot, prompt, convert_func=str, allow_zero=False):
        """Helper function to get user input with type conversion."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(prompt)
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            content = msg.content.strip()

            # Convert input if necessary
            if convert_func in (int, float):
                value = convert_func(content)
                if value == 0 and not allow_zero:
                    await ctx.send("❌ Zero is not a valid option here. Try again.")
                    return None
                return value
            return content
        except ValueError:
            await ctx.send("❌ Invalid input. Please enter a valid number.")
            return None
        except Exception:
            await ctx.send("❌ Timed out. Please try again.")
            return None
