"""functions that help the player run commands"""
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