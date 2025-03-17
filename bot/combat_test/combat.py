"""Defines the rules of combat"""

# pylint: disable= line-too-long
import asyncio
from random import randint, choice
import discord
from discord.ext import commands
import discord.ext
from psycopg2.extensions import connection
from bot.database_utils import DatabaseConnection
from bot.combat_test.status_effects import (Paralyze,
                    Frozen,
                    Burning,
                    Poisoned,
                    Charmed,
                    Regenerating,
                    Blessed,
                    Confusion,
                    ManaBoost,
                    HealthBoost,
                    ExtremeSpeed,
                    Armor,
                    Taunt,
                    Leech,
                    FireWeakness,
                    WaterWeakness,
                    EarthWeakness,
                    AirWeakness
)
class Player:
    """A Player object for each character in the game"""
    def __init__(self, user: discord.User, conn: connection, cog: commands.Cog):
        self.cog = cog
        self.user = user
        self.id = user.id
        self.name = user.name
        self.mention = user.mention
        self.mana_hidden = False
        self.data = self.get_character_data(conn)
        self.char_name = self.data.get('character_name')
        self.max_health = self.data.get('health')
        self.health = self.data.get('health')
        self.max_mana = self.data.get('mana')
        self.mana = self.data.get('mana')
        self.speed = self.data.get('speed')
        self.image = self.data.get('image_url', None)
        self.race_name = self.data.get('race_name')
        self.class_name = self.data.get('class_name')
        self.status_effects = []

        # self.attack_power = random.randint(5, 10)
        self.spells = [
            Spell(
                self,
                spell.get('spell_name'),
                spell.get('spell_power'),
                spell.get('mana_cost'),
                spell.get('cooldown'),
                spell.get('element_name'),
                spell.get('status_name'),
                spell.get('chance'),
                spell.get('duration'),
                spell.get('spell_type_name')
            )
            for spell in self.get_equipped_spells(conn)
        ]

        self.inventory = [
            Item(item.get('item_name'),
                Spell(self,
                    item.get('spell_name'),
                    item.get('spell_power'),
                    0, # Mana cost
                    item.get('cooldown'),
                    item.get('element_name'),
                    item.get('status_name'),
                    item.get('chance'),
                    item.get('duration'),
                    item.get('spell_type_name')),
                item.get('spell_charges')
            )
            for item in self.get_enchanted_inventory(conn)
        ]


    def get_character_data(self, conn: connection) -> dict:
        """Gets data for the selected player character"""
        with conn.cursor() as cursor:
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
                            cl.class_name,
                            r.speed
                    FROM character AS c
                    JOIN race AS r ON c.race_id = r.race_id
                    JOIN class AS cl ON c.class_id = cl.class_id
                    WHERE c.player_id = (
                        SELECT player_id FROM player WHERE player_name = %s
                    AND selected_character = TRUE
                    );
                """, (self.name,))
            return cursor.fetchone()

    def take_damage(self, damage: int):
        """Player takes damage equal to damage variable"""
        self.health -= damage
        return self.health <= 0

    def get_equipped_spells(self, conn: connection) -> list[dict]:
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
                    sa.duration,
                    st.spell_type_name
                FROM character c
                JOIN player p ON c.player_id = p.player_id
                JOIN character_spell_assignment csa ON c.character_id = csa.character_id
                JOIN spells s ON csa.spell_id = s.spell_id
                JOIN element e ON s.element_id = e.element_id
                LEFT JOIN spell_status_spell_assignment sa ON s.spell_id = sa.spell_id
                LEFT JOIN spell_status ss ON sa.spell_status_id = ss.spell_status_id
                JOIN spell_type st ON s.spell_type_id = st.spell_type_id
                WHERE p.player_name = %s
                AND c.selected_character = TRUE
                ORDER BY sa.spell_status_spell_assignment_id DESC
                LIMIT 4;
                """
        with conn.cursor() as cursor:
            cursor.execute(query, (self.name,))
            return cursor.fetchall()
    
    def get_enchanted_inventory(self, conn: connection) -> list[dict]:
        """Gets the inventory of the selected character that contains enchanted items using the player_name"""

        query = """
            SELECT 
                i.item_name,
                i.spell_charges,
                s.spell_name,
                s.spell_power,
                s.cooldown,
                e.element_name,
                ss.status_name,
                sa.chance,
                sa.duration,
                st.spell_type_name
            FROM character c
            JOIN player p ON c.player_id = p.player_id
            JOIN inventory inv ON c.character_id = inv.character_id
            JOIN item i ON inv.inventory_id = i.inventory_id
            JOIN spells s ON i.spell_id = s.spell_id
            JOIN element e ON s.element_id = e.element_id
            LEFT JOIN spell_status_spell_assignment sa ON s.spell_id = sa.spell_id
            LEFT JOIN spell_status ss ON sa.spell_status_id = ss.spell_status_id
            JOIN spell_type st ON s.spell_type_id = st.spell_type_id
            WHERE p.player_name = %s
            AND c.selected_character = TRUE
            AND i.spell_id IS NOT NULL
            ORDER BY i.item_name;
        """

        with conn.cursor() as cursor:
            cursor.execute(query, (self.name,))
            return cursor.fetchall()


    def get_exp(self, conn: connection, experience: int):
        """Adds experience to the player"""
        with conn.cursor() as cursor:
            cursor.execute("""
                        WITH selected_character AS (
                            SELECT c.character_id
                            FROM "character" c
                            JOIN player p ON c.player_id = p.player_id
                            WHERE p.player_name = %s
                            AND c.selected_character = TRUE
                        )
                        UPDATE "character"
                        SET experience = experience + %s
                        WHERE character_id IN (SELECT character_id FROM selected_character)
                        RETURNING experience;
                           """, (self.name, experience))
            new_experience = cursor.fetchone().get('experience')
            conn.commit()
            return f"""{self.mention} has received **{experience:.1f}** experience points!
            They now have **{new_experience:.1f}** experience!"""

    def show_exp(self, conn: connection) -> int:
        """Returns their current amount of xp"""
        with conn.cursor() as cursor:
            cursor.execute("""
                            SELECT c.experience
                            FROM "character" c
                            JOIN player p ON c.player_id = p.player_id
                            WHERE p.player_name = %s
                            AND c.selected_character = TRUE
                        """, (self.name,))
            return int(cursor.fetchone().get('experience'))


class Spell:
    """A Spell object that can be cast to damage a player or to inflict a status effect on them"""
    def __init__(self,
                 caster: str,
                 name: str,
                 power: int,
                 cost: int,
                 cooldown: int,
                 element: str,
                 status: str,
                 chance: int,
                 duration: int,
                 spell_type: str):
        self.caster = caster
        self.name = name
        self.power = power
        self.cost = cost
        self.cooldown = cooldown
        self.element = element
        self.status = self.get_status(status, chance, duration)
        self.spell_type = spell_type

    def get_status(self, status, chance, duration):
        """Returns the correct object for the status type"""
        status_map = {
            "None": None,
            "Paralyze": Paralyze,
            "Frozen": Frozen,
            "Burning": Burning,
            "Poisoned": Poisoned,
            "Charmed": Charmed,
            "Regenerating": Regenerating,
            "Blessed": Blessed,
            "Confusion": Confusion,
            "Mana Boost": ManaBoost,
            "Health Boost": HealthBoost,
            "Extreme Speed": ExtremeSpeed,
            "Armor": Armor,
            "Taunt": Taunt,
            "Fire Weakness": FireWeakness,
            "Water Weakness": WaterWeakness,
            "Earth Weakness": EarthWeakness,
            "Air Weakness": AirWeakness,
            "Leech": Leech,
        }
        status_class = status_map.get(status)

        return status_class(self.caster, self.power, chance, duration) if status_class else None


    def cast(self, caster: Player, targets: list[Player] | Player):
        """Casts the spell on the target(s)"""

        # If a single target is provided, convert it to a list for uniform handling
        if isinstance(targets, Player):
            targets = [targets]

        caster.mana -= self.cost
        results = []

        for target in targets:
            if self.status:
                results.append(self.status.apply_status(target))
            else:
                results.append(target.take_damage(self.power))

        return results


    def get_targets(self, caster: Player, players: list[Player]) -> list[Player]:
        """Determines valid targets for a spell"""
        # Initialize the list of targets based on the spell type
        if self.spell_type == "Single Target":
            targets = [caster] + players
        elif self.spell_type == "Area of Effect":

            targets = players
        elif self.spell_type == "Passive":
            targets = [caster]
        else:
            targets = players

        for status in caster.status_effects:
            if hasattr(status, 'change_targets'):
                targets = status.change_targets(
                    caster, targets)

        return targets


class Item:
    """An item object that has a spell enchantment that a player can use"""

    def __init__(self, name: str, spell: Spell, charges: int):
        self.name = name
        self.spell = spell
        self.charges = charges

    def use(self, target: Player):
        """Lets the player use the items effect on the target."""
        return self.effect(target)

    def effect(self):
        """Users the spell effect"""
        pass


class Combat(commands.Cog):
    """Defines the combat class that will determine the phase of the combat
    and invoke effects that push the flow of the game

    When the !combat command is made their should be a button that allows
    players to join with their selected character,
    When a player joins a message only they can see will say,
    you joined the battle with (SELECTED CHARACTER NAME) and the
    message should update with how many people have joined the battle;


    The game will have phases:
    - Standby Phase; Characters roll a die
    to determine who goes first with priority given to those with a higher speed.
    - Status Phase; the turn player will take the impact of all status effects
    they are currently effected by and the status duration goes down.
    - Attack Phase; The turn player chooses either spell (choose a spell),
    item (choose an item to use), meditate (regenerate mana), Run (Concede the battle).
    - Target Phase; if the player chose item or spell.
    then choose a target to cast the spell or item on.

    For each choice the player should be presented with buttons."""
    def __init__(self, bot: commands.Bot, conn: connection):
        self.bot = bot
        self.conn = conn
        self.active_battles = {}
        print('Combat cog loaded')

    @commands.command()
    async def combat(self, ctx):
        """Commands the flow of combat by initializing the encounter"""
        battle_id = ctx.channel.id
        self.active_battles[battle_id] = {
            "players": [],
            "turn_order": [],
            "current_turn": None,
            "status_effects": {},
            "enemy": None,
            "experience": 0,
        }

        battle_message = await ctx.send("A battle is starting! Click 'Join' to enter.")
        view = JoinBattleView(self, ctx, battle_id, battle_message)

        await battle_message.edit(view=view)


    async def start_battle(self, ctx: commands.Context, battle_id: int):
        """Starts the battle by setting players and turn order"""
        battle = self.active_battles[battle_id]
        players = battle["players"]

        # if len(players) < 2:
        #     enemy = EnemyAI()
        #     battle["enemy"] = enemy
        #     players.append(enemy)
        #     await ctx.send(f"An enemy AI has joined the battle: {enemy.name}!")

        turn_order = sorted(players, key=lambda p: randint(
            1, 20) + p.speed, reverse=True)

        battle["turn_order"] = turn_order
        battle["current_turn"] = turn_order[0]

        await ctx.send(f"""Battle has begun! {turn_order[0].mention
                                            if hasattr(turn_order[0], 'mention')
                                            else turn_order[0].name} goes first.""")

        await self.next_turn(ctx, battle_id)

    async def next_turn(self, ctx: commands.Context, battle_id: int):
        """The flow of combat"""
        battle = self.active_battles[battle_id]
        turn_order = battle["turn_order"]
        battle["turn_order"] = [
            player for player in turn_order if player.health > 0]

        turn_order = battle["turn_order"]


        if len(turn_order) <= 1:
            for player in battle.get('players'):
                await ctx.send(player.get_exp(self.conn, battle["experience"]))
            winner = turn_order[0] if turn_order else None
            await ctx.send(f'Because they won, {winner.get_exp(self.conn, battle["experience"])}')
            message = (
                f"The battle is over! {winner.mention if hasattr(winner, 'mention') else winner.name} is the winner!"
                if winner
                else "The battle has ended with no winner."
            )
            await ctx.send(message)
            del self.active_battles[battle_id]
            return

        current_player = turn_order.pop(0)
        battle["current_turn"] = current_player
        turn_order.append(current_player)

        for status_effect in current_player.status_effects:
            await ctx.send(f'{status_effect.reduce_status(current_player)}')

        for spell in current_player.spells:
            # If Passive, cast immediately
            if spell.spell_type == "Passive":
                if current_player.mana > spell.cost:
                    result = spell.cast(current_player, current_player)
                    asyncio.create_task(ctx.send(
                        f"{current_player.mention} Passive effect activates **{spell.name}**!\n{result[0] if result else ''}"))
                else:
                    asyncio.create_task(ctx.send(
                        f"{current_player.mention} Passive effect **{spell.name}** fails to activate!"))
        # Generate Health & Mana Bars
        def generate_bar(value, max_value, length=10):
            """Generates bars for health and mana"""
            filled = int((value / max_value) * length)
            return f"[{'█' * filled}{' ' * (length - filled)}] {value:.2f}/{max_value:.2f}"

        health_bar = generate_bar(
            current_player.health, current_player.max_health)
        mana_bar = generate_bar(current_player.mana, current_player.max_mana)

        embed = discord.Embed(
            title=f"{current_player.char_name}'s Turn", description=f"Whats your move {current_player.char_name}", color=discord.Color.blue())
        if current_player.image:
            embed.set_thumbnail(url=current_player.image)
        embed.add_field(name="Health", value=health_bar, inline=False)
        embed.add_field(name="Mana", value=mana_bar, inline=False)
        for i, status in enumerate(current_player.status_effects):
            embed.add_field(name=f"Status {i+1}", value=status.status, inline=False)

        if isinstance(current_player, EnemyAI):
            await current_player.take_action(ctx, self, battle_id)
        else:
            targets = turn_order[:-1]
            await ctx.send(embed=embed, view=ActionView(self, ctx, battle_id, current_player, targets))


class EnemyAI:
    """An Enemy AI object that will make moves against human players"""
    def __init__(self):
        self.name = "Goblin Warrior"
        self.health = 20
        self.attack_damage = randint(3, 7)

    async def take_action(self, ctx: commands.Context, cog: Combat, battle_id: int):
        """Lets the NPC choose a player and attack them"""
        battle = cog.active_battles[battle_id]
        players = [p for p in battle["players"] if not isinstance(p, EnemyAI)]
        if not players:
            return

        target = choice(players)
        await ctx.send(f"{self.name} attacks {target.mention} for {self.attack_damage} damage!")
        await cog.next_turn(ctx, battle_id)


class JoinBattleView(discord.ui.View):
    """The View that Players will be presented with to join combat"""
    def __init__(self, cog: Combat, ctx: commands.Context, battle_id: int, battle_message: str):
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.battle_id = battle_id
        self.battle_message = battle_message
        self.players = []

    @discord.ui.button(label="Join Battle", style=discord.ButtonStyle.green)
    async def join_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """A Button that allows the player to join combat"""
        
        user = interaction.user
        if user in self.players:
            await interaction.response.send_message("You've already joined!", ephemeral=True)
            return

        player = Player(user, self.cog.conn, self.cog)
        

        self.players.append(user)
        self.cog.active_battles[self.battle_id]["players"].append(player)
        self.cog.active_battles[self.battle_id]["experience"] += max(
            (player.show_exp(self.cog.conn) / 10), 50)

        await self.battle_message.edit(content=f"{len(self.players)} players have joined the battle.")
        await interaction.response.send_message("You joined the battle!", ephemeral=True)



    @discord.ui.button(label="Start Battle", style=discord.ButtonStyle.blurple)
    async def start_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Lets the players start combat with the number of players that has joined"""
        if len(self.players) > 1:
            await self.cog.start_battle(self.ctx, self.battle_id)
        else:
            await interaction.response.send_message("You need another player to start the battle", ephemeral=True)


    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Stops battle if they change their mind"""
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the battle initiator can cancel!", ephemeral=True)
            return

        del self.cog.active_battles[self.battle_id]
        await self.battle_message.edit(content="The battle has been canceled.", view=None)
        await interaction.response.send_message("Battle canceled.", ephemeral=True)


class ActionView(discord.ui.View):
    """View for player actions.
    Casting a spell
    Using an item
    Meditating
    or Fleeing"""

    def __init__(self, cog: Combat, ctx: commands.Context, battle_id: int, player: Player, targets: list[Player]):
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.battle_id = battle_id
        self.player = player
        self.targets = targets

    @discord.ui.button(label="Attack", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Attack action"""
        if interaction.user != self.player.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        await interaction.response.send_message(f"{self.player.mention} attacks!", ephemeral=False)
        await self.cog.next_turn(self.ctx, self.battle_id)

    @discord.ui.button(label="Spell", style=discord.ButtonStyle.blurple)
    async def spell(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Spell action"""
        if interaction.user != self.player.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        await interaction.response.send_message("Choose a spell!", view=SpellSelectionView(self.ctx, self.player, self.targets, self.battle_id), ephemeral=True)


    @discord.ui.button(label="Item", style=discord.ButtonStyle.green)
    async def item(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Item action"""
        if interaction.user != self.player.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        await interaction.response.send_message("Choose an item!", view=ItemSelectionView(self.ctx, self.player, self.targets, self.battle_id), ephemeral=True)

    @discord.ui.button(label="Meditate", style=discord.ButtonStyle.gray)
    async def meditate(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Regenerate mana"""

        if interaction.user != self.player.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        restore = randint(int(self.player.max_mana // 3),
                            int(self.player.max_mana))

        self.player.mana += restore
        self.player.mana = min(self.player.mana, self.player.max_mana)
        await interaction.response.send_message(f"{self.player.mention} meditates and restores {restore} mana!\nCurrent Mana {self.player.mana}/{self.player.max_mana}", ephemeral=False)

        await self.cog.next_turn(self.ctx, self.battle_id)

    @discord.ui.button(label="Run", style=discord.ButtonStyle.danger)
    async def run(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Concede the battle"""
        if interaction.user != self.player.user:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return

        await interaction.response.send_message(f"{self.player.mention} flees the battle!", ephemeral=False)
        self.cog.active_battles[self.battle_id]["turn_order"].remove(
            self.player)

        await self.cog.next_turn(self.ctx, self.battle_id)


async def setup(bot: commands.Bot):
    """Sets up the combat cog with a database connection.
    This allows the commands to be used by the Discord bot"""
    conn = DatabaseConnection.get_connection()
    await bot.add_cog(Combat(bot, conn))


class ItemSelectionView(discord.ui.View):
    """Creates a button foe each item"""

    def __init__(self, ctx: commands.Command, player: Player, targets: list[Player], battle_id: int, timeout = 60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.player = player
        self.targets = targets
        self.battle_id = battle_id

        for item in self.player.inventory:
            # No need for passives to get a button
            if item.spell.spell_type != "Passive":
                self.add_item(SpellButton(self.ctx, item.spell, self.player, self.targets, self.battle_id))

class SpellSelectionView(discord.ui.View):
    """Dynamically creates buttons for each spell"""

    def __init__(self, ctx: commands.Context, player: Player, targets: list[Player], battle_id: int, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.player = player
        self.targets = targets
        self.battle_id = battle_id

        # Create a button for each spell
        for spell in self.player.spells:
            # If Passive, cast immediately
            if spell.spell_type != "Passive":
                self.add_item(SpellButton(self.ctx, spell, self.player, self.targets, self.battle_id))


class SpellButton(discord.ui.Button):
    """Button representing a spell"""

    def __init__(self, ctx: commands.Context, spell: Spell, player: Player, targets: list[Player], battle_id: int):
        super().__init__(label=f'{spell.name}\n({spell.cost if player.mana_hidden is False else '???'}) mana', style=discord.ButtonStyle.green)
        self.ctx = ctx
        self.spell = spell
        self.player = player
        self.targets = targets
        self.battle_id = battle_id

    async def callback(self, interaction: discord.Interaction):
        """Step 1: Player selects a spell"""
        await interaction.response.defer()

        if self.player.mana < self.spell.cost:
            await interaction.followup.send("You don't have enough mana to cast this spell!", ephemeral=True)
            await self.player.cog.next_turn(self.ctx, self.battle_id)
        else:
            # Step 2: Open target selection menu
            view = TargetSelectionView(self.ctx, self.spell, self.player, self.targets, self.battle_id)
            await interaction.followup.send("Choose your target:", view=view, ephemeral=True)


class TargetSelectionView(discord.ui.View):
    """Creates buttons for choosing a target"""

    def __init__(self, ctx: commands.Context, spell: Spell, caster: Player, players: list[Player], battle_id: int, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.spell = spell
        self.caster = caster
        self.battle_id = battle_id

        # Determine valid targets
        if spell.spell_type == "Area of Effect":
            self.add_item(AOETargetButton(
                ctx, spell, players, caster, battle_id))
        else:
            # Create a button for each individual target for single-target spells
            targets = spell.get_targets(caster, players)
            for target in targets:
                self.add_item(TargetButton(
                    ctx, spell, target, caster, battle_id))


class TargetButton(discord.ui.Button):
    """Button representing a target"""

    def __init__(self, ctx: commands.Context, spell: Spell, target: Player, caster: Player, battle_id: int):
        super().__init__(label=target.user.display_name, style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.spell = spell
        self.target = target
        self.caster = caster
        self.battle_id = battle_id

    async def callback(self, interaction: discord.Interaction):
        """Step 3: Player selects a target, spell is cast"""
        await interaction.response.defer()
        result = self.spell.cast(self.caster, self.target)  # Call spell logic

        await interaction.followup.send(f"{self.caster.mention} casts **{self.spell.name}** on {self.target.mention}!\n{result if result and isinstance(result, str) else ""}")
        await self.caster.cog.next_turn(self.ctx, self.battle_id)
        if result is True:
            await self.ctx.send(f'{self.target.mention} has fainted')



class AOETargetButton(discord.ui.Button):
    """Button representing an Area of Effect spell"""

    def __init__(self, ctx: commands.Context, spell: Spell, targets: list[Player], caster: Player, battle_id: int):
        super().__init__(label="Cast on all targets", style=discord.ButtonStyle.red)
        self.ctx = ctx
        self.spell = spell
        self.targets = targets
        self.caster = caster
        self.battle_id = battle_id

    async def callback(self, interaction: discord.Interaction):
        """Casts the AOE spell when clicked"""

        await interaction.response.defer()

        # Cast the spell on all valid targets
        results = self.spell.cast(self.caster, self.targets)
        result_text = "\n".join(
            [f"{target.name}: {result}" for target,
                result in zip(self.targets, results)]
        )

        await interaction.followup.send(f"{self.caster.mention} casts **{self.spell.name}** on everyone!\n{result_text}")

        await self.caster.cog.next_turn(self.ctx, self.battle_id)

        # Check if any targets fainted
        for target in self.targets:
            if target.health <= 0:
                await self.ctx.send(f"{target.mention} has fainted!")
