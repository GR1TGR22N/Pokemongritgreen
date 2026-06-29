import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import random
import asyncio

# ========== BOT SETUP ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== SAVE SYSTEM ==========
DEFAULT_SAVE = {
    "party": [
        {
            "name": "Zorua", "level": 10, "hp": 22, "max_hp": 22,
            "nature": "Hasty", "types": "Normal/Ghost", "shiny": True,
            "ability": "Illusion", "held": "Leftovers",
            "moves": [
                {"name": "Scratch", "type": "Normal", "bp": 40, "pp": 29, "max_pp": 35},
                {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 24, "max_pp": 30},
                {"name": "Astonish", "type": "Ghost", "bp": 30, "pp": 13, "max_pp": 15}
            ]
        },
        {
            "name": "Mankey", "level": 7, "hp": 26, "max_hp": 26,
            "nature": "Jolly", "types": "Fighting", "shiny": False,
            "ability": "Vital Spirit", "held": None,
            "moves": [
                {"name": "Scratch", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35},
                {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30},
                {"name": "Low Kick", "type": "Fighting", "bp": "Var", "pp": 20, "max_pp": 20}
            ]
        },
        {
            "name": "Rattata", "level": 5, "hp": 20, "max_hp": 20,
            "nature": "Adamant", "types": "Normal", "shiny": False,
            "ability": "Guts", "held": None,
            "moves": [
                {"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35},
                {"name": "Tail Whip", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30},
                {"name": "Quick Attack", "type": "Normal", "bp": 40, "pp": 30, "max_pp": 30}
            ]
        },
        {
            "name": "Nidoran", "level": 7, "hp": 24, "max_hp": 24,
            "nature": "Naughty", "types": "Poison", "shiny": False,
            "ability": "Poison Point", "held": None,
            "moves": [
                {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30},
                {"name": "Peck", "type": "Flying", "bp": 35, "pp": 35, "max_pp": 35}
            ]
        },
        {
            "name": "Caterpie", "level": 5, "hp": 20, "max_hp": 20,
            "nature": "Modest", "types": "Bug", "shiny": False,
            "ability": "Shield Dust", "held": None,
            "moves": [
                {"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35},
                {"name": "String Shot", "type": "Bug", "bp": "Stat", "pp": 40, "max_pp": 40}
            ]
        }
    ],
    "inventory": {"poke_balls": 2, "potions": 0, "antidotes": 2},
    "money": 320,
    "location": "Viridian Forest"
}

SAVE_FILE = "save.json"

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_SAVE.copy()

def save_game(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

save = load_save()
active_battles = {}

# ========== UTILITIES ==========
def hp_bar(current, maximum):
    pct = current / maximum
    filled = round(pct * 4)
    return f"HP {'█' * filled}{'░' * (4 - filled)} {int(pct * 100)}%"

def party_display():
    lines = ["**Your Team**\n"]
    for i, mon in enumerate(save["party"], 1):
        shiny = "✨ " if mon.get("shiny") else ""
        held = f"  {mon['held']}" if mon.get("held") else ""
        lines.append(f"**{i}. {shiny}{mon['name']}**  Lv.{mon['level']}{held}")
        lines.append(f"{mon['types']}  {mon['nature']}  {mon['ability']}")
        lines.append(hp_bar(mon["hp"], mon["max_hp"]))
        for move in mon["moves"]:
            bp = f"{move['bp']} BP" if isinstance(move['bp'], int) else move['bp']
            lines.append(f"　{move['name']}  {move['type']}  {bp}  {move['pp']}/{move['max_pp']} PP")
        lines.append("")
    return "\n".join(lines)

# ========== ENCOUNTER TABLES (KANTO) ==========
ENCOUNTERS = {
    "Route 1": [
        {"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"},
        {"name": "Rattata", "level": (2, 4), "types": "Normal"}
    ],
    "Route 2": [
        {"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"},
        {"name": "Rattata", "level": (2, 5), "types": "Normal"},
        {"name": "Caterpie", "level": (3, 5), "types": "Bug"},
        {"name": "Weedle", "level": (3, 5), "types": "Bug/Poison"}
    ],
    "Route 22": [
        {"name": "Rattata", "level": (2, 5), "types": "Normal"},
        {"name": "Spearow", "level": (3, 5), "types": "Normal/Flying"},
        {"name": "Mankey", "level": (3, 5), "types": "Fighting"},
        {"name": "Nidoran♀", "level": (4, 6), "types": "Poison"},
        {"name": "Nidoran♂", "level": (4, 6), "types": "Poison"}
    ],
    "Viridian Forest": [
        {"name": "Caterpie", "level": (3, 6), "types": "Bug"},
        {"name": "Weedle", "level": (3, 6), "types": "Bug/Poison"},
        {"name": "Metapod", "level": (4, 7), "types": "Bug"},
        {"name": "Kakuna", "level": (4, 7), "types": "Bug/Poison"},
        {"name": "Pikachu", "level": (4, 7), "types": "Electric", "rare": True}
    ],
    "Pewter City": [],
    "Viridian City": [],
    "Pallet Town": []
}

LOCATIONS = {
    "Pallet Town": {"north": "Route 1"},
    "Route 1": {"north": "Viridian City", "south": "Pallet Town"},
    "Viridian City": {"north": "Route 2", "south": "Route 1", "west": "Route 22"},
    "Route 2": {"north": "Pewter City", "south": "Viridian City", "east": "Viridian Forest"},
    "Route 22": {"east": "Viridian City"},
    "Viridian Forest": {"west": "Route 2"},
    "Pewter City": {"south": "Route 2"}
}

# ========== BATTLE SYSTEM ==========
class BattleView(View):
    def __init__(self, user_id, wild_mon):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.wild = wild_mon
        self.active = save["party"][0]  # First party member
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This isn't your battle.", ephemeral=True)
            return False
        return True
    
    def build_embed(self):
        lines = []
        w = self.wild
        a = self.active
        
        lines.append(f"**Wild {w['name']}**  Lv.{w['level']}  {w['types']}")
        lines.append(hp_bar(w['hp'], w['max_hp']))
        lines.append("")
        lines.append(f"**{a['name']}**  Lv.{a['level']}  {a['types']}")
        lines.append(hp_bar(a['hp'], a['max_hp']))
        lines.append("")
        for i, move in enumerate(a["moves"], 1):
            bp = f"{move['bp']} BP" if isinstance(move['bp'], int) else move['bp']
            lines.append(f"{i}. {move['name']}  {move['type']}  {bp}  {move['pp']}/{move['max_pp']} PP")
        
        embed = discord.Embed(title="Battle!", description="\n".join(lines), color=0x50C878)
        return embed
    
    def build_buttons(self):
        self.clear_items()
        for i, move in enumerate(self.active["moves"], 1):
            disabled = move["pp"] <= 0
            btn = Button(label=f"{i}. {move['name']}", row=0, disabled=disabled)
            btn.callback = self.make_callback(i)
            self.add_item(btn)
        
        bag_btn = Button(label="Bag", row=1, style=discord.ButtonStyle.secondary)
        bag_btn.callback = self.bag_callback
        self.add_item(bag_btn)
        
        run_btn = Button(label="Run", row=1, style=discord.ButtonStyle.danger)
        run_btn.callback = self.run_callback
        self.add_item(run_btn)
    
    def make_callback(self, move_idx):
        async def callback(interaction: discord.Interaction):
            await self.do_turn(interaction, move_idx - 1)
        return callback
    
    async def bag_callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Bag coming soon!", ephemeral=True)
    
    async def run_callback(self, interaction: discord.Interaction):
        del active_battles[self.user_id]
        await interaction.response.edit_message(content="Got away safely!", embed=None, view=None)
    
    async def do_turn(self, interaction: discord.Interaction, move_idx):
        active = self.active
        wild = self.wild
        move = active["moves"][move_idx]
        
        if move["pp"] <= 0:
            await interaction.response.send_message("No PP left!", ephemeral=True)
            return
        
        # Player attacks
        move["pp"] -= 1
        bp = move["bp"] if isinstance(move["bp"], int) else 40
        damage = max(1, int((active["level"] * bp / 30) * random.uniform(0.85, 1.0)))
        wild["hp"] -= damage
        
        lines = [f"**{active['name']}** used **{move['name']}**!"]
        if wild["hp"] <= 0:
            wild["hp"] = 0
            lines.append(f"Wild {wild['name']} fainted!")
            lines.append(f"**{active['name']}** gained some experience!")
            del active_battles[self.user_id]
            save_game(save)
            await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None)
            return
        
        lines.append(f"Wild {wild['name']} took damage!")
        
        # Wild attacks (simple)
        w_damage = max(1, int((wild["level"] * 20 / 30) * random.uniform(0.85, 1.0)))
        active["hp"] -= w_damage
        lines.append(f"Wild **{wild['name']}** attacked!")
        
        if active["hp"] <= 0:
            active["hp"] = 0
            lines.append(f"**{active['name']}** fainted!")
            del active_battles[self.user_id]
            save_game(save)
            await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None)
            return
        
        self.build_buttons()
        embed = self.build_embed()
        await interaction.response.edit_message(content="\n".join(lines), embed=embed, view=self)

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online as {bot.user}")

# ========== SLASH COMMANDS ==========
@bot.tree.command(name="party", description="View your Pokémon team")
async def party(interaction: discord.Interaction):
    await interaction.response.send_message(party_display())

@bot.tree.command(name="inventory", description="Check your bag and money")
async def inventory(interaction: discord.Interaction):
    inv = save["inventory"]
    lines = [
        "**Your Bag**\n",
        f"Poké Balls: {inv['poke_balls']}",
        f"Potions: {inv['potions']}",
        f"Antidotes: {inv['antidotes']}",
        f"Money: ₽{save['money']}",
        f"Location: {save['location']}"
    ]
    await interaction.response.send_message("\n".join(lines))

@bot.tree.command(name="heal", description="Restore your team to full HP and PP")
async def heal(interaction: discord.Interaction):
    for mon in save["party"]:
        mon["hp"] = mon["max_hp"]
        for move in mon["moves"]:
            move["pp"] = move["max_pp"]
    save_game(save)
    await interaction.response.send_message("✅ Your team has been fully healed.")

@bot.tree.command(name="explore", description="Look for wild Pokémon in the current area")
async def explore(interaction: discord.Interaction):
    loc = save["location"]
    table = ENCOUNTERS.get(loc, [])
    
    if not table:
        await interaction.response.send_message(f"No wild Pokémon here. Try a route or forest.")
        return
    
    user_id = interaction.user.id
    if user_id in active_battles:
        await interaction.response.send_message("You're already in a battle!", ephemeral=True)
        return
    
    # Pick random encounter
    encounter = random.choice(table)
    level = random.randint(*encounter["level"])
    # Shiny check
    shiny = random.randint(1, 4096) == 1
    max_hp = 15 + level * 3
    
    wild_mon = {
        "name": encounter["name"],
        "level": level,
        "types": encounter["types"],
        "hp": max_hp,
        "max_hp": max_hp,
        "shiny": shiny
    }
    
    shiny_text = "✨ " if shiny else ""
    
    view = BattleView(user_id, wild_mon)
    active_battles[user_id] = view
    view.build_buttons()
    embed = view.build_embed()
    
    await interaction.response.send_message(
        f"{shiny_text}Wild **{encounter['name']}** appeared! Lv.{level}",
        embed=embed,
        view=view
    )

@bot.tree.command(name="move", description="Travel to a new location")
async def move(interaction: discord.Interaction, direction: str):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    
    direction = direction.lower()
    if direction in connections:
        save["location"] = connections[direction]
        save_game(save)
        await interaction.response.send_message(f"You traveled {direction} to **{save['location']}**.")
    else:
        dirs = ", ".join(connections.keys())
        await interaction.response.send_message(f"Can't go {direction} from here. Options: {dirs}")

@move.autocomplete("direction")
async def move_autocomplete(interaction: discord.Interaction, current: str):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    return [discord.app_commands.Choice(name=f"{d} → {loc_name}", value=d) for d, loc_name in connections.items()]

@bot.tree.command(name="map", description="See where you are and where you can go")
async def map_cmd(interaction: discord.Interaction):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    lines = [f"**Current Location:** {loc}\n", "**You can go:**"]
    for d, dest in connections.items():
        lines.append(f"{d} → {dest}")
    if not connections:
        lines.append("Nowhere from here.")
    await interaction.response.send_message("\n".join(lines))

# ========== RUN BOT ==========
bot.run(os.environ["DISCORD_TOKEN"])
