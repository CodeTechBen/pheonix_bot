"""functions that gets the primary keys of tables from the database"""

from datetime import datetime
import discord
from discord.ext import commands
from psycopg2.extensions import connection

class DatabaseMapper:
    """This defines the functions that get the mappings from the database"""

    @classmethod
    def get_player_mapping(cls, conn: connection, server_id: int) -> dict[str, int]:
        """Returns a dictionary of player names and their DB ID number for a specific server"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT player_name, player_id FROM player WHERE server_id = %s", (
                    server_id,)
            )
            return {row["player_name"]: row["player_id"] for row in cursor.fetchall()}


    @classmethod
    def get_location_mapping(cls, conn: connection, server_id: int) -> dict[int, int]:
        """Gets the channel id and the location id in a dictionary"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT channel_id, location_id FROM location WHERE server_id = %s", (
                    server_id,)
            )
            return {row["channel_id"]: row["location_id"] for row in cursor.fetchall()}


    @classmethod
    def get_settlement_mapping(cls, conn: connection, server_id: int) -> dict[int: int]:
        """Gets the thread id and settlement id in a dictionary"""
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT thread_id, settlement_id FROM settlements WHERE server_id = %s", (
                    server_id,)
            )
            return {row["thread_id"]: row["settlement_id"] for row in cursor.fetchall()}


    @classmethod
    def get_character_mapping(cls, conn: connection, player_id: int) -> dict[int, int]:
        """Gets a dictionary for {character_name : character_id} for a specific player"""
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT character_name, character_id
                FROM character
                WHERE player_id = %s""", (player_id,)
            )
            return {row['character_name']: row['character_id'] for row in cursor.fetchall()}


    @classmethod
    def get_race_map(cls, conn: connection, server_id: int) -> dict[str: int]:
        """Gets a dictionary of {race_name: race_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT race_name, race_id
                        FROM race
                        WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
                        )
            return {row['race_name']: row['race_id'] for row in cursor.fetchall()}


    @classmethod
    def get_class_map(cls, conn: connection, server_id: int) -> dict[str: int]:
        """Gets a dictionary of {race_name: race_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT class_name, class_id
                        FROM class
                        WHERE server_id = %s AND is_playable = TRUE""", (server_id,)
                        )
            return {row['class_name']: row['class_id'] for row in cursor.fetchall()}


    @classmethod
    def get_element_map(cls, conn: connection) -> dict[str: int]:
        """gets a dictionary of {element_name: element_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT element_name, element_id
                        FROM element""")
            return {row['element_name']: row['element_id'] for row in cursor.fetchall()}


    @classmethod
    def get_spell_status_map(cls, conn: connection) -> dict[str: int]:
        """Gets a dictionary of {spell_status_name: spell_status_id}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT status_name, spell_status_id
                        FROM spell_status""")
            return {row['status_name']: row['spell_status_id'] for row in cursor.fetchall()}


    @classmethod
    def get_spell_type_map(cls, conn: connection) -> dict[str: int]:
        """Gets a dictionary of spell types {spell_type_id: spell_type_name}"""
        with conn.cursor() as cursor:
            cursor.execute("""SELECT spell_type_id, spell_type_name
                        FROM spell_type""")
            return {row['spell_type_id']: row['spell_type_name'] for row in cursor.fetchall()}


    @classmethod
    def get_last_event(cls, conn: connection, player_name: str, event_name: str) -> datetime:
        """Gets the last time the selected character performed a specific event"""
        print('getting last event')
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
    def get_craft_skill(cls, conn: connection, player_name: str) -> dict[str: int]:
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
    def get_equipped_spells(cls, conn: connection, ctx: commands.Context) -> list[dict]:
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
    def get_players_characters(cls, conn: connection, ctx: commands.Context) -> list[dict]:
        """Returns a list of all characters, including race_name and class_name, each entry is a dictionary"""
        with conn.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT c.player_id,
                            c.character_id,
                            c.character_name,
                            c.health,
                            c.mana,
                            c.craft_skill,
                            c.shards,
                            c.experience,
                            c.image_url,
                            r.race_name,
                            cl.class_name
                    FROM character AS c
                    JOIN race AS r ON c.race_id = r.race_id
                    JOIN class AS cl ON c.class_id = cl.class_id
                    WHERE c.player_id = (
                        SELECT player_id FROM player WHERE player_name = %s
                    );
                """, (ctx.author.name,))
            except Exception as e:
                print(e)
            return cursor.fetchall()


    @classmethod
    def get_potential_player_spells(cls, conn: connection, ctx: commands.Context) -> list[dict]:
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
    def fetch_selected_character_id(cls, conn: connection, player_name: str):
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
    def get_player_id(cls, conn: connection, player_name: str, server_id: int):
        """Fetches the player_id based on player_name and server_id."""
        print('get player id')
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT player_id 
                FROM player 
                WHERE player_name = %s AND server_id = %s
            """, (player_name, server_id))
            player = cursor.fetchone()
            return player.get('player_id') if player else None


    @classmethod
    def get_selected_character_id(cls, conn: connection, player_id: int) -> int:
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
    def get_inventory_id(cls, conn, character_id: int):
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
    def get_items_in_inventory(cls, conn: connection, inventory_id: int) -> list[dict]:
        """Fetches all items in the specified inventory, including spell and element details if enchanted."""
        print('getting items in inventory')
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT i.item_id, i.item_name, i.value, i.spell_id,
                    s.spell_name, s.spell_description, s.spell_power, 
                    s.mana_cost, s.cooldown, s.scaling_factor, 
                    e.element_name, s.spell_type_id, 
                    s.race_id, s.class_id
                FROM item i
                LEFT JOIN spells s ON i.spell_id = s.spell_id
                LEFT JOIN element e ON s.element_id = e.element_id
                WHERE i.inventory_id = %s;
            """, (inventory_id,))

            items = cursor.fetchall()

        return [dict(item) for item in items]


    
    @classmethod
    def get_non_enchanted_items_in_inventory(cls, conn: connection, inventory_id: int) -> dict:
        """Fetches all items in the specified inventory."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT item_id, item_name, value 
                FROM item 
                WHERE inventory_id = %s
                AND spell_id IS NULL;
            """, (inventory_id,))
            return cursor.fetchall()
    
    @classmethod
    def sell_item(cls, conn, item_id: int, player_name: str) -> bool:
        """Removes an item from the inventory and adds shards to the player."""
        print(f'item_id: {item_id}')
        print(f'player_name: {player_name}')
        try:
            with conn.cursor() as cursor:
                # Get item value
                cursor.execute(
                    "SELECT value FROM item WHERE item_id = %s", (item_id,))
                result = cursor.fetchone()
                if not result:
                    return False
                print(result)
                item_value = result.get('value')
                print(item_value)
                # Get character ID
                cursor.execute("SELECT character_id FROM character WHERE player_id = (SELECT player_id FROM player WHERE player_name = %s) LIMIT 1",
                            (player_name,))
                result = cursor.fetchone()
                character_id = result.get('character_id')
                print(character_id)
                # Remove item from inventory
                cursor.execute(
                    "DELETE FROM item WHERE item_id = %s", (item_id,))

                # Add shards to character
                cursor.execute(
                    "UPDATE character SET shards = shards + %s WHERE character_id = %s", (item_value, character_id))

                cursor.execute(
                    "SELECT event_type_id FROM event_type WHERE event_name = 'Sell';"
                )

                result = cursor.fetchone()
                event_type_id = result.get('event_type_id')
                print(event_type_id)
                
                # Add buying event to Database

                cursor.execute("""
                INSERT INTO character_event (character_id, item_id, event_type_id)
                VALUES (%s, %s, %s);
                """, (character_id, item_id, event_type_id))


                conn.commit()
                return True
        except Exception as e:
            print(f"Error selling item: {e}")
            conn.rollback()
            return False
    
    @classmethod
    def buy_item(cls, conn: connection, item_id: int, seller_name: str, buyer_name: str, value: int) -> bool:
        """
        Checks if the buyer has enough shards to buy the item.
        Transfers the item from the seller's inventory to the buyer's inventory.
        Deducts the amount from the buyer and adds it to the seller's shards.
        """
        try:
            with conn.cursor() as cursor:
                # Get buyer character_id
                cursor.execute("""
                    SELECT c.character_id 
                    FROM character AS c
                    JOIN player AS p ON p.player_id = c.player_id
                    WHERE p.player_name = %s AND c.selected_character = TRUE
                """, (buyer_name,))
                buyer_character_id = cursor.fetchone()

                if not buyer_character_id:
                    return False

                buyer_character_id = buyer_character_id.get('character_id')

                # Get seller character_id
                cursor.execute("""
                    SELECT c.character_id 
                    FROM character AS c
                    JOIN player AS p ON p.player_id = c.player_id
                    WHERE p.player_name = %s AND c.selected_character = TRUE
                """, (seller_name,))
                seller_character_id = cursor.fetchone()

                if not seller_character_id:
                    return False  # Seller does not have a selected character

                seller_character_id = seller_character_id.get('character_id')

                # Check if buyer has enough shards
                cursor.execute(
                    "SELECT shards FROM character WHERE character_id = %s", (buyer_character_id,))
                buyer_shards = cursor.fetchone()

                if not buyer_shards or buyer_shards.get('shards') < value:
                    return False  # Buyer does not have enough shards

                # Transfer the item to the buyer's inventory
                cursor.execute("""
                    UPDATE "item"
                    SET inventory_id = (
                        SELECT i.inventory_id
                        FROM inventory AS i
                        WHERE i.character_id = %s
                        LIMIT 1
                    ), is_selling = FALSE, listed_value = NULL
                    WHERE item_id = %s
                """, (buyer_character_id, item_id))

                # Deduct shards from buyer
                cursor.execute("""UPDATE character SET shards = shards - %s WHERE character_id = %s""",
                            (value, buyer_character_id))

                # Add shards to seller
                cursor.execute("""UPDATE character SET shards = shards + %s WHERE character_id = %s""",
                            (value, seller_character_id))
                
                # Retrieve event_type_id for "Buy"
                cursor.execute(
                    "SELECT event_type_id FROM event_type WHERE event_name = 'Buy';")
                buy_event = cursor.fetchone()
                buy_event_id = buy_event.get('event_type_id') if buy_event else None

                # Retrieve event_type_id for "Sell"
                cursor.execute(
                    "SELECT event_type_id FROM event_type WHERE event_name = 'Sell';")
                sell_event = cursor.fetchone()
                sell_event_id = sell_event.get('event_type_id') if sell_event else None
                
                # Log event for buyer (Buy event)
                cursor.execute("""
                    INSERT INTO character_event (character_id, item_id, event_type_id)
                    VALUES (%s, %s, %s);
                """, (buyer_character_id, item_id, buy_event_id))

                # Log event for seller (Sell event)
                cursor.execute("""
                    INSERT INTO character_event (character_id, item_id, event_type_id)
                    VALUES (%s, %s, %s);
                """, (seller_character_id, item_id, sell_event_id))

                # Commit transaction
                conn.commit()
                return True

        except Exception as e:
            conn.rollback()
            print(f"Error processing item purchase: {e}")
            return False



    @classmethod
    def set_sellable_item(cls, conn: connection, item_id: int, value: int) -> bool:
        """Sets an item as sellable and sets the listed_value as value"""
        try:
            with conn.cursor() as cursor:
                # Update the is_selling status to True and set the listed_value
                cursor.execute("""
                    UPDATE "item"
                    SET "is_selling" = TRUE, "listed_value" = %s
                    WHERE "item_id" = %s
                """, (value, item_id))

                # Commit the transaction
                conn.commit()

                # Check if any row was updated
                if cursor.rowcount > 0:
                    return True
                return False
        except Exception as e:
            conn.rollback()
            print(f"Error setting item as sellable: {e}")
            return False

    @classmethod
    def get_marketplace(cls, conn: connection) -> dict:
        """Gets all items classified as being sold"""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT i.item_id, i.item_name, i.listed_value, 
                    c.character_name, p.player_name, 
                    s.spell_name  -- Fetch spell name if enchanted
                FROM item AS i
                JOIN inventory AS inv ON i.inventory_id = inv.inventory_id
                JOIN character AS c ON inv.character_id = c.character_id
                JOIN player AS p ON c.player_id = p.player_id
                LEFT JOIN spells AS s ON i.spell_id = s.spell_id
                WHERE i.is_selling = TRUE;
                """)
            return cursor.fetchall()



class EmbedHelper:
    """Handles creating embeds for displaying data in Discord"""

    @classmethod
    def create_map_embed(cls,
                         title: str,
                         description: str,
                         data_dict: dict,
                         color: str) -> discord.Embed:
        """Creates an embed message for Discord with selectable options."""
        embed = discord.Embed(
            title=title, description=description, color=color)
        for name, _id in data_dict.items():
            embed.add_field(name=f"🔹 {name}",
                            value=f"ID: `{_id}`", inline=False)
        return embed


    @classmethod
    def create_inventory_embed(cls, ctx: commands.Context, items: list[dict]) -> discord.Embed:
        """Creates an embed to display the inventory items, including spell details if enchanted."""
        print('getting inventory embed')
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s Inventory",
            description="Here are the items in your inventory:",
            color=discord.Color.blue()
        )

        for item in items:
            item_name = item.get('item_name')
            shards = item.get('value')

            # Base item details
            item_value_text = f"Value: {shards} {'shard' if shards == 1 else 'shards'}"
            spell_text = ""

            # Add spell details if enchanted
            if item.get('spell_id'):
                spell_text = (
                    f"\n✨ **Enchanted with:** {item.get('spell_name')}\n"
                    f"📖 *{item.get('spell_description')}*\n"
                    f"💥 Power: {item.get('spell_power')} | 🔥 Element: {item.get('element_name')}\n"
                    f"⏳ Cooldown: {item.get('cooldown')} | 🎚️ Scaling: {item.get('scaling_factor')}"
                )

            embed.add_field(
                name=f"{item_name.title().replace('_', ' ')}",
                value=item_value_text + spell_text,
                inline=False
            )

        return embed



class UserInputHelper:
    """Handles user input prompts and conversions"""

    @classmethod
    async def get_input(cls,
                        ctx: commands.Context,
                        bot: commands.bot.Bot,
                        prompt: str,
                        convert_func=str,
                        allow_zero: bool = False):
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


class SpellQuery:
    """Handles queries on spells."""


class SpellQuery:
    """Handles queries on spells."""


class SpellQuery:
    """Handles queries on spells."""

    @classmethod
    def get_spell_difficulty(cls,
                        spell_power: int,
                        mana: int,
                        cooldown: int,
                        scaling_factor: float,
                        spell_status_chance: int,
                        spell_duration: int) -> int:
        """Base value calculation"""
        base_difficulty = (max(spell_power, 10) * max(scaling_factor, 0.7)) / 5
        print(f'base_difficulty = {base_difficulty}')
        # Cooldown penalty
        cooldown_penalty = max(0.5, 1.2 - (cooldown / 12))
        base_difficulty *= cooldown_penalty
        print(f'cooldown_penalty = {cooldown_penalty}')
        print(f'base_difficulty = {base_difficulty}')
        # Status effects significantly increase difficulty
        # 100% status → 4x multiplier
        status_bonus = max(1, spell_status_chance / 25)
        base_difficulty *= status_bonus
        print(f'status_bonus = {status_bonus}')
        print(f'base_difficulty = {base_difficulty}')
        # Duration scaling: Now more punishing for long durations
        duration_penalty = 4.0 ** (spell_duration)  # Grows faster
        base_difficulty *= duration_penalty
        print(f'duration_penalty = {duration_penalty}')
        print(f'base_difficulty = {base_difficulty}')
        # Mana scaling: Encourages efficiency
        mana_factor = max(0.8, 2.5 - (mana / 40))
        base_difficulty *= mana_factor
        print(f'mana_factor = {mana_factor}')
        print(f'base_difficulty = {base_difficulty}')

        return int(min(base_difficulty, 1000))  # Cap at 1000

    @classmethod
    def get_crafting_chance(cls, craft_skill: int, spell_difficulty: int) -> float:
        """Calculates the chance to craft a spell"""
        chance = (craft_skill / (spell_difficulty * 2)) * 100
        return min(chance, 95.0)  # Cap at 95%


if __name__ == "__main__":
    pass
    # spell_power = 1
    # mana = 50
    # cooldown = 1
    # scaling_factor = 1
    # spell_status_chance = 50
    # spell_duration = 3

    # spell_difficulty = SpellQuery.get_spell_difficulty(
    #     spell_power, mana, cooldown, scaling_factor, spell_status_chance, spell_duration
    # )

    # craft_skill = 100
    # crafting_chance = SpellQuery.get_crafting_chance(craft_skill, spell_difficulty)

    # print(f"Spell Value: {spell_difficulty} Gold")
    # print(f"Crafting Chance: {crafting_chance:.2f}%")
