import discord


async def get_input(ctx, bot, prompt, convert_func=str, allow_zero=False):
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


def create_embed(title, description, data_dict, color):
    """Creates an embed message for Discord with selectable options."""
    embed = discord.Embed(title=title, description=description, color=color)
    for name, _id in data_dict.items():
        embed.add_field(name=f"🔹 {name}", value=f"ID: `{_id}`", inline=False)
    return embed


def get_player_id(conn, player_name: str, server_id: int):
    """Fetches the player_id based on player_name and server_id."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT player_id 
            FROM player 
            WHERE player_name = %s AND server_id = %s
        """, (player_name, server_id))
        player = cursor.fetchone()
        return player.get('player_id') if player else None


def get_character_id(conn, player_id: int):
    """Fetches the character_id for the selected character."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT character_id 
            FROM character 
            WHERE player_id = %s AND selected_character = TRUE
        """, (player_id,))
        character = cursor.fetchone()
        return character.get('character_id') if character else None


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


def get_items_in_inventory(conn, inventory_id: int):
    """Fetches all items in the specified inventory."""
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT item_id, item_name, value 
            FROM item 
            WHERE inventory_id = %s
        """, (inventory_id,))
        return cursor.fetchall()


def create_inventory_embed(ctx, items):
    """Creates an embed to display the inventory items."""
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Inventory",
        description="Here are the items in your inventory:",
        color=discord.Color.blue()
    )

    for item in items:
        embed.add_field(name=f"{item.get('item_name').title().replace('_', ' ')}",
                        value=f"Value: {item.get('value')} {'shard' if item.get('value') == 1 else 'shards'}",
                        inline=False)
        embed.add_field(name='ID: ', value=item.get('item_id'))
    return embed

if __name__ == "__main__":
    pass