"""functions that help the player run commands"""
from random import randint
from datetime import datetime
from psycopg2.extensions import connection

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


def add_spell_to_character(conn: connection, ctx, selected_spell_id):
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


def increase_wallet(conn: connection, player_name: str, profit: int) -> str:
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


def update_last_event(conn: connection, player_name: str, event_name: str, timestamp: datetime):
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
    
def insert_item_player_inventory(conn: connection, item_name: str, item_value: int, character_id: int) -> int:
    """Inserts an item into a characters inventory"""
    with conn.cursor as cursor:
        # Insert item into inventory
        query = """
                INSERT INTO item (item_name, value, inventory_id)
                VALUES (%s, %s, (SELECT inventory_id FROM inventory WHERE character_id = %s))
                RETURNING item_id;
                """
        cursor.execute(query, (item_name, item_value, character_id))
        conn.commit()

    return cursor.fetchone().get('item_id')

def create_item(conn: connection, player_name: str, item_name: str, item_value: int) -> str:
    """Attempts to create an item based on the player's craft skill."""
    result = get_craft_skill(conn, player_name)
    character_id = result.get('character_id')
    craft_skill = result.get('craft_skill')

    # Determine crafting success chance
    success_chance = min(
        (craft_skill / (item_value * 2)) * 100, 95)
    roll = randint(1, 100)

    if roll > success_chance:
        return f"{player_name}, your crafting attempt failed! Try again later."
    item_id = insert_item_player_inventory(conn, item_name, item_value)
    return f"{player_name} successfully crafted '{item_name}' (Value: {item_value})! 🎉"
