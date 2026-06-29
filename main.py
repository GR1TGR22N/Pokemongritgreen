import discord
from discord.ext import commands
from discord.ui import Button, View
import json
import os
import random
import math

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

DEFAULT_SAVE = {
    "party": [
        {"name": "Zorua", "level": 10, "hp": 22, "max_hp": 22, "nature": "Hasty", "types": "Normal/Ghost", "shiny": True, "ability": "Illusion", "held": "Leftovers", "moves": [{"name": "Scratch", "type": "Normal", "bp": 40, "pp": 29, "max_pp": 35}, {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 24, "max_pp": 30}, {"name": "Astonish", "type": "Ghost", "bp": 30, "pp": 13, "max_pp": 15}]},
        {"name": "Mankey", "level": 7, "hp": 26, "max_hp": 26, "nature": "Jolly", "types": "Fighting", "shiny": False, "ability": "Vital Spirit", "held": None, "moves": [{"name": "Scratch", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Low Kick", "type": "Fighting", "bp": "Var", "pp": 20, "max_pp": 20}]},
        {"name": "Rattata", "level": 5, "hp": 20, "max_hp": 20, "nature": "Adamant", "types": "Normal", "shiny": False, "ability": "Guts", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "Tail Whip", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Quick Attack", "type": "Normal", "bp": 40, "pp": 30, "max_pp": 30}]},
        {"name": "Nidoran", "level": 7, "hp": 24, "max_hp": 24, "nature": "Naughty", "types": "Poison", "shiny": False, "ability": "Poison Point", "held": None, "moves": [{"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Peck", "type": "Flying", "bp": 35, "pp": 35, "max_pp": 35}]},
        {"name": "Caterpie", "level": 5, "hp": 20, "max_hp": 20, "nature": "Modest", "types": "Bug", "shiny": False, "ability": "Shield Dust", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "String Shot", "type": "Bug", "bp": "Stat", "pp": 40, "max_pp": 40}]}
    ],
    "inventory": {"poke_balls": 2, "potions": 0, "antidotes": 2},
    "money": 320,
    "location": "Viridian Forest",
    "box": []
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

def hp_bar(current, maximum):
    pct = max(0, min(1, current / maximum))
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

ENCOUNTERS = {
    "Route 1": [{"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"}, {"name": "Rattata", "level": (2, 4), "types": "Normal"}],
    "Route 2": [{"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"}, {"name": "Rattata", "level": (2, 5), "types": "Normal"}, {"name": "Caterpie", "level": (3, 5), "types": "Bug"}, {"name": "Weedle", "level": (3, 5), "types": "Bug/Poison"}],
    "Route 22": [{"name": "Rattata", "level": (2, 5), "types": "Normal"}, {"name": "Spearow", "level": (3, 5), "types": "Normal/Flying"}, {"name": "Mankey", "level": (3, 5), "types": "Fighting"}, {"name": "Nidoran♀", "level": (4, 6), "types": "Poison"}, {"name": "Nidoran♂", "level": (4, 6), "types": "Poison"}],
    "Viridian Forest": [{"name": "Caterpie", "level": (3, 6), "types": "Bug"}, {"name": "Weedle", "level": (3, 6), "types": "Bug/Poison"}, {"name": "Metapod", "level": (4, 7), "types": "Bug"}, {"name": "Kakuna", "level": (4, 7), "types": "Bug/Poison"}, {"name": "Pikachu", "level": (4, 7), "types": "Electric", "rare": True}],
    "Pewter City": [], "Viridian City": [], "Pallet Town": []
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

NATURES = ["Adamant", "Jolly", "Modest", "Timid", "Naughty", "Hasty", "Calm", "Bold", "Impish", "Careful", "Rash", "Mild", "Quiet", "Brave", "Relaxed", "Sassy"]

def catch_rate(wild_mon):
    max_hp = wild_mon["max_hp"]
    current_hp = wild_mon["hp"]
    rate = 190 if wild_mon["name"] == "Pikachu" else 255
    a = ((3 * max_hp - 2 * current_hp) * rate) / (3 * max_hp)
    b = 1048560 / math.sqrt(math.sqrt(16711680 / a))
    return min(255, int(b))

class BattleView(View):
    def __init__(self, user_id, wild_mon):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.wild = wild_mon
        self.active = save["party"][0]
        self.message = None
    
    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your battle.", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        if self.user_id in active_battles:
            del active_battles[self.user_id]
    
    def build_embed(self):
        w = self.wild
        a = self.active
        shiny = "✨ " if w.get("shiny") else ""
        lines = [f"{shiny}Wild **{w['name']}**  Lv.{w['level']}  {w['types']}", hp_bar(w['hp'], w['max_hp']), "", f"**{a['name']}**  Lv.{a['level']}  {a['types']}", hp_bar(a['hp'], a['max_hp']), ""]
        for i, move in enumerate(a["moves"], 1):
            bp = f"{move['bp']} BP" if isinstance(move['bp'], int) else move['bp']
            lines.append(f"{i}. {move['name']}  {move['type']}  {bp}  {move['pp']}/{move['max_pp']} PP")
        return discord.Embed(title="⚔️ Battle!", description="\n".join(lines), color=0x50C878)
    
    def build_buttons(self):
        self.clear_items()
        for i, move in enumerate(self.active["moves"], 1):
            btn = Button(label=f"{i}. {move['name']}", row=0, disabled=(move["pp"] <= 0))
            btn.callback = self.make_move_callback(i)
            self.add_item(btn)
        catch_btn = Button(label="🎯 Catch", row=1, style=discord.ButtonStyle.success, disabled=(save["inventory"]["poke_balls"] <= 0))
        catch_btn.callback = self.catch_callback
        self.add_item(catch_btn)
        run_btn = Button(label="🏃 Run", row=1, style=discord.ButtonStyle.danger)
        run_btn.callback = self.run_callback
        self.add_item(run_btn)
    
    def make_move_callback(self, move_idx):
        async def callback(interaction: discord.Interaction):
            active = self.active
            wild = self.wild
            move = active["moves"][move_idx - 1]
            
            if move["pp"] <= 0:
                await interaction.response.send_message("No PP left!", ephemeral=True)
                return
            
            move["pp"] -= 1
            bp = move["bp"] if isinstance(move["bp"], int) else 40
            damage = max(1, int((active["level"] * bp / 30) * random.uniform(0.85, 1.0)))
            wild["hp"] = max(0, wild["hp"] - damage)
            
            lines = [f"**{active['name']}** used **{move['name']}**!"]
            
            if wild["hp"] <= 0:
                lines.append(f"Wild {wild['name']} fainted!")
                if self.user_id in active_battles:
                    del active_battles[self.user_id]
                save_game(save)
                await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None)
                return
            
            w_damage = max(1, int((wild["level"] * 20 / 30) * random.uniform(0.85, 1.0)))
            active["hp"] = max(0, active["hp"] - w_damage)
            lines.append(f"Wild **{wild['name']}** attacked!")
            
            if active["hp"] <= 0:
                lines.append(f"**{active['name']}** fainted!")
                if self.user_id in active_battles:
                    del active_battles[self.user_id]
                save_game(save)
                await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None)
                return
            
            self.build_buttons()
            await interaction.response.edit_message(content="\n".join(lines), embed=self.build_embed(), view=self)
        return callback
    
    async def catch_callback(self, interaction: discord.Interaction):
        inv = save["inventory"]
        if inv["poke_balls"] <= 0:
            await interaction.response.send_message("No Poké Balls left!", ephemeral=True)
            return
        
        inv["poke_balls"] -= 1
        rate = catch_rate(self.wild)
        shakes = sum(1 for _ in range(3) if random.randint(0, 255) < rate)
        shake_text = ["...", "......", "........."]
        
        if shakes == 3:
            msg = f"🟢 You threw a Poké Ball!\n{shake_text[0]}\n{shake_text[1]}\n{shake_text[2]}\n**Gotcha! {self.wild['name']} was caught!**"
            new_mon = {"name": self.wild["name"], "level": self.wild["level"], "hp": self.wild["max_hp"], "max_hp": self.wild["max_hp"], "nature": random.choice(NATURES), "types": self.wild["types"], "shiny": self.wild.get("shiny", False), "ability": "Standard", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}]}
            if len(save["party"]) < 6:
                save["party"].append(new_mon)
                msg += f"\n{self.wild['name']} added to your party!"
            else:
                save["box"].append(new_mon)
                msg += f"\n{self.wild['name']} sent to PC box!"
            if self.user_id in active_battles:
                del active_battles[self.user_id]
            save_game(save)
            await interaction.response.edit_message(content=msg, embed=None, view=None)
        else:
            msg = f"🔴 You threw a Poké Ball!\n" + "\n".join(shake_text[:shakes]) + "\nOh no! It broke free!"
            self.build_buttons()
            await interaction.response.edit_message(content=msg, embed=self.build_embed(), view=self)
    
    async def run_callback(self, interaction: discord.Interaction):
        if self.user_id in active_battles:
            del active_battles[self.user_id]
        await interaction.response.edit_message(content="Got away safely!", embed=None, view=None)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online as {bot.user}")

@bot.tree.command(name="party", description="View your Pokémon team")
async def party(interaction: discord.Interaction):
    await interaction.response.send_message(party_display())

@bot.tree.command(name="inventory", description="Check your bag")
async def inventory(interaction: discord.Interaction):
    inv = save["inventory"]
    await interaction.response.send_message(f"**Your Bag**\n\nPoké Balls: {inv['poke_balls']}\nPotions: {inv['potions']}\nAntidotes: {inv['antidotes']}\nMoney: ₽{save['money']}\nLocation: {save['location']}")

@bot.tree.command(name="heal", description="Restore your team")
async def heal(interaction: discord.Interaction):
    for mon in save["party"]:
        mon["hp"] = mon["max_hp"]
        for move in mon["moves"]:
            move["pp"] = move["max_pp"]
    save_game(save)
    await interaction.response.send_message("✅ Team fully healed!")

@bot.tree.command(name="explore", description="Look for wild Pokémon")
async def explore(interaction: discord.Interaction):
    loc = save["location"]
    table = ENCOUNTERS.get(loc, [])
    if not table:
        await interaction.response.send_message("No wild Pokémon here.")
        return
    if interaction.user.id in active_battles:
        await interaction.response.send_message("Already in a battle!", ephemeral=True)
        return
    
    encounter = random.choice(table)
    level = random.randint(*encounter["level"])
    shiny = random.randint(1, 4096) == 1
    wild_mon = {"name": encounter["name"], "level": level, "types": encounter["types"], "hp": 15 + level * 3, "max_hp": 15 + level * 3, "shiny": shiny}
    
    view = BattleView(interaction.user.id, wild_mon)
    active_battles[interaction.user.id] = view
    view.build_buttons()
    
    shiny_text = "✨ " if shiny else ""
    await interaction.response.send_message(f"{shiny_text}Wild **{encounter['name']}** appeared! Lv.{level}", embed=view.build_embed(), view=view)

@bot.tree.command(name="move", description="Travel to a new location")
async def move(interaction: discord.Interaction, direction: str):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    direction = direction.lower()
    if direction in connections:
        save["location"] = connections[direction]
        save_game(save)
        await interaction.response.send_message(f"Traveled {direction} to **{save['location']}**.")
    else:
        await interaction.response.send_message(f"Can't go {direction}. Options: {', '.join(connections.keys())}")

@move.autocomplete("direction")
async def move_autocomplete(interaction: discord.Interaction, current: str):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    return [discord.app_commands.Choice(name=f"{d} → {loc_name}", value=d) for d, loc_name in connections.items()]

@bot.tree.command(name="map", description="View your location")
async def map_cmd(interaction: discord.Interaction):
    loc = save["location"]
    connections = LOCATIONS.get(loc, {})
    lines = [f"**{loc}**\n"]
    for d, dest in connections.items():
        lines.append(f"{d} → {dest}")
    await interaction.response.send_message("\n".join(lines) if connections else f"**{loc}**\nNowhere to go.")

@bot.tree.command(name="box", description="View PC box")
async def box_cmd(interaction: discord.Interaction):
    box = save.get("box", [])
    if not box:
        await interaction.response.send_message("PC box is empty.")
        return
    lines = [f"**PC Box ({len(box)} Pokémon)**\n"]
    for i, mon in enumerate(box, 1):
        shiny = "✨ " if mon.get("shiny") else ""
        lines.append(f"{i}. {shiny}{mon['name']} Lv.{mon['level']} {mon['types']}")
    await interaction.response.send_message("\n".join(lines))

bot.run(os.environ["DISCORD_TOKEN"])
