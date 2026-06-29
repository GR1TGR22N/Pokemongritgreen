import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import os
import random
import math

# ========== BOT SETUP ==========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== SAVE SYSTEM ==========
DEFAULT_SAVE = {
    "party": [
        {"name": "Nidoran ♂", "level": 8, "hp": 28, "max_hp": 28, "exp": 0, "nature": "Naughty", "types": "Poison", "shiny": False, "ability": "Poison Point", "held": None, "moves": [{"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Peck", "type": "Flying", "bp": 35, "pp": 35, "max_pp": 35}]},
        {"name": "Zorua ♂", "level": 10, "hp": 28, "max_hp": 28, "exp": 0, "nature": "Hasty", "types": "Normal/Ghost", "shiny": True, "ability": "Illusion", "held": "Leftovers", "moves": [{"name": "Scratch", "type": "Normal", "bp": 40, "pp": 25, "max_pp": 35}, {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Astonish", "type": "Ghost", "bp": 30, "pp": 14, "max_pp": 15}]},
        {"name": "Mankey ♂", "level": 7, "hp": 26, "max_hp": 26, "exp": 0, "nature": "Jolly", "types": "Fighting", "shiny": False, "ability": "Vital Spirit", "held": None, "moves": [{"name": "Scratch", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "Leer", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Low Kick", "type": "Fighting", "bp": "Var", "pp": 20, "max_pp": 20}]},
        {"name": "Rattata ♂", "level": 5, "hp": 20, "max_hp": 20, "exp": 0, "nature": "Adamant", "types": "Normal", "shiny": False, "ability": "Guts", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "Tail Whip", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}, {"name": "Quick Attack", "type": "Normal", "bp": 40, "pp": 30, "max_pp": 30}]},
        {"name": "Caterpie ♀", "level": 5, "hp": 20, "max_hp": 20, "exp": 0, "nature": "Modest", "types": "Bug", "shiny": False, "ability": "Shield Dust", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}, {"name": "String Shot", "type": "Bug", "bp": "Stat", "pp": 40, "max_pp": 40}]},
        {"name": "Metapod ♀", "level": 6, "hp": 22, "max_hp": 22, "exp": 0, "nature": "Modest", "types": "Bug", "shiny": False, "ability": "Shed Skin", "held": None, "moves": [{"name": "Harden", "type": "Normal", "bp": "Stat", "pp": 30, "max_pp": 30}]}
    ],
    "inventory": {"poke_balls": 0, "potions": 0, "antidotes": 2},
    "money": 270,
    "location": "Pewter City",
    "box": [],
    "badges": [],
    "story_flags": {
        "blue_mocked_and_left": True, "leaf_egg_hatched": True,
        "daisy_oak_gave_shiny_charm": True, "viridian_center_visited": True,
        "red_missing": True, "leaf_missing": True,
        "knows_dr_vane_name": True, "viridian_forest_beaten": True,
        "viridian_trainer_house_done": True, "pokedex_empty": True,
        "met_aurora": True, "aurora_near_gym": True,
        "brock_defeated": False, "brock_first_attempt": True
    }
}

SAVE_FILE = "save.json"

def load_save():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            for key in DEFAULT_SAVE:
                if key not in data:
                    data[key] = DEFAULT_SAVE[key]
            if "story_flags" not in data:
                data["story_flags"] = DEFAULT_SAVE["story_flags"]
            return data
    return DEFAULT_SAVE.copy()

def save_game(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)

save = load_save()
active_battles = {}

# ========== UTILITIES ==========
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

def first_alive():
    for i, mon in enumerate(save["party"]):
        if mon["hp"] > 0:
            return i
    return None

# ========== TYPE CHART ==========
def type_multiplier(attack_type, defender_types):
    chart = {
        "Normal": {"Rock": 0.5, "Ghost": 0, "Steel": 0.5},
        "Fire": {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 2, "Bug": 2, "Rock": 0.5, "Dragon": 0.5, "Steel": 2},
        "Water": {"Fire": 2, "Water": 0.5, "Grass": 0.5, "Ground": 2, "Rock": 2, "Dragon": 0.5},
        "Electric": {"Water": 2, "Electric": 0.5, "Grass": 0.5, "Ground": 0, "Flying": 2, "Dragon": 0.5},
        "Grass": {"Fire": 0.5, "Water": 2, "Grass": 0.5, "Poison": 0.5, "Ground": 2, "Flying": 0.5, "Bug": 0.5, "Rock": 2, "Dragon": 0.5, "Steel": 0.5},
        "Ice": {"Fire": 0.5, "Water": 0.5, "Ice": 0.5, "Grass": 2, "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": 0.5},
        "Fighting": {"Normal": 2, "Ice": 2, "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Rock": 2, "Ghost": 0, "Dark": 2, "Steel": 2, "Fairy": 0.5},
        "Poison": {"Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5, "Steel": 0, "Fairy": 2},
        "Ground": {"Fire": 2, "Grass": 0.5, "Electric": 2, "Poison": 2, "Flying": 0, "Bug": 0.5, "Rock": 2, "Steel": 2},
        "Flying": {"Grass": 2, "Electric": 0.5, "Fighting": 2, "Bug": 2, "Rock": 0.5, "Steel": 0.5},
        "Psychic": {"Fighting": 2, "Psychic": 0.5, "Steel": 0.5, "Dark": 0},
        "Bug": {"Fire": 0.5, "Grass": 2, "Fighting": 0.5, "Poison": 0.5, "Flying": 0.5, "Psychic": 2, "Ghost": 0.5, "Dark": 2, "Steel": 0.5, "Fairy": 0.5},
        "Rock": {"Fire": 2, "Ice": 2, "Fighting": 0.5, "Ground": 0.5, "Flying": 2, "Bug": 2, "Steel": 0.5},
        "Ghost": {"Normal": 0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
        "Dragon": {"Dragon": 2, "Steel": 0.5, "Fairy": 0},
        "Dark": {"Fighting": 0.5, "Psychic": 2, "Ghost": 2, "Dark": 0.5, "Fairy": 0.5},
        "Steel": {"Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Ice": 2, "Rock": 2, "Steel": 0.5, "Fairy": 2},
        "Fairy": {"Fire": 0.5, "Fighting": 2, "Poison": 0.5, "Dragon": 2, "Dark": 2, "Steel": 0.5}
    }
    defender_list = defender_types.split("/")
    mult = 1.0
    for def_type in defender_list:
        if def_type in chart.get(attack_type, {}):
            mult *= chart[attack_type][def_type]
    return mult

# ========== EXP / LEVEL UP / EVOLUTION ==========
def exp_to_next(level):
    return int(level ** 1.5 * 8)

def level_up(mon):
    old_level = mon["level"]
    msg = ""
    while mon["exp"] >= exp_to_next(mon["level"]):
        mon["exp"] -= exp_to_next(mon["level"])
        mon["level"] += 1
        mon["max_hp"] += random.randint(1, 3)
        mon["hp"] = mon["max_hp"]
        msg += f"\n⬆️ **{mon['name']}** grew to Lv.{mon['level']}!"
    if mon["level"] > old_level:
        msg += check_evolution(mon)
        msg += learn_new_moves(mon)
    return msg

def check_evolution(mon):
    evolves = {
        "Caterpie": (7, "Metapod"), "Metapod": (10, "Butterfree"),
        "Weedle": (7, "Kakuna"), "Kakuna": (10, "Beedrill"),
        "Pidgey": (18, "Pidgeotto"), "Rattata": (20, "Raticate"),
        "Spearow": (20, "Fearow"), "Nidoran ♂": (16, "Nidorino"),
        "Nidoran ♀": (16, "Nidorina"), "Mankey": (28, "Primeape")
    }
    base_name = mon["name"].replace(" ♂", "").replace(" ♀", "")
    if base_name in evolves:
        evo_level, evo_name = evolves[base_name]
        if mon["level"] >= evo_level:
            old_name = mon["name"]
            mon["name"] = evo_name
            return f"\n🎉 **{old_name}** evolved into **{evo_name}**!"
    return ""

def learn_new_moves(mon):
    move_list = {
        "Butterfree": [(10, "Confusion", "Psychic", 50, 25), (12, "Sleep Powder", "Grass", "Stat", 15)],
        "Beedrill": [(10, "Fury Attack", "Normal", 15, 20)],
        "Pidgeotto": [(18, "Gust", "Flying", 40, 35)],
        "Raticate": [(20, "Hyper Fang", "Normal", 80, 15)],
        "Fearow": [(20, "Fury Attack", "Normal", 15, 20)],
        "Nidorino": [(16, "Horn Attack", "Normal", 65, 25)],
        "Primeape": [(28, "Cross Chop", "Fighting", 100, 5)]
    }
    learned = ""
    if mon["name"] in move_list:
        for lvl, move_name, move_type, bp, pp in move_list[mon["name"]]:
            if mon["level"] >= lvl and move_name not in [m["name"] for m in mon["moves"]]:
                if len(mon["moves"]) < 4:
                    mon["moves"].append({"name": move_name, "type": move_type, "bp": bp, "pp": pp, "max_pp": pp})
                learned += f"\n📖 **{mon['name']}** learned **{move_name}**!"
    return learned

# ========== ENCOUNTERS & LOCATIONS ==========
ENCOUNTERS = {
    "Route 1": [{"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"}, {"name": "Rattata", "level": (2, 4), "types": "Normal"}],
    "Route 2": [{"name": "Pidgey", "level": (2, 5), "types": "Normal/Flying"}, {"name": "Rattata", "level": (2, 5), "types": "Normal"}, {"name": "Caterpie", "level": (3, 5), "types": "Bug"}, {"name": "Weedle", "level": (3, 5), "types": "Bug/Poison"}],
    "Route 22": [{"name": "Rattata", "level": (2, 5), "types": "Normal"}, {"name": "Spearow", "level": (3, 5), "types": "Normal/Flying"}, {"name": "Mankey", "level": (3, 5), "types": "Fighting"}, {"name": "Nidoran ♀", "level": (4, 6), "types": "Poison"}, {"name": "Nidoran ♂", "level": (4, 6), "types": "Poison"}],
    "Viridian Forest": [{"name": "Caterpie", "level": (3, 6), "types": "Bug"}, {"name": "Weedle", "level": (3, 6), "types": "Bug/Poison"}, {"name": "Metapod", "level": (4, 7), "types": "Bug"}, {"name": "Kakuna", "level": (4, 7), "types": "Bug/Poison"}, {"name": "Pikachu", "level": (4, 7), "types": "Electric", "rare": True}],
    "Route 3": [{"name": "Pidgey", "level": (6, 12), "types": "Normal/Flying"}, {"name": "Spearow", "level": (6, 12), "types": "Normal/Flying"}, {"name": "Mankey", "level": (8, 12), "types": "Fighting"}, {"name": "Jigglypuff", "level": (5, 9), "types": "Normal/Fairy", "rare": True}],
    "Pewter City": [], "Viridian City": [], "Pallet Town": []
}

LOCATIONS = {
    "Pallet Town": {"north": "Route 1"},
    "Route 1": {"north": "Viridian City", "south": "Pallet Town"},
    "Viridian City": {"north": "Route 2", "south": "Route 1", "west": "Route 22"},
    "Route 2": {"north": "Pewter City", "south": "Viridian City", "east": "Viridian Forest"},
    "Route 22": {"east": "Viridian City"},
    "Viridian Forest": {"west": "Route 2"},
    "Pewter City": {"south": "Route 2", "east": "Route 3"}
}

NATURES = ["Adamant", "Jolly", "Modest", "Timid", "Naughty", "Hasty", "Calm", "Bold", "Impish", "Careful"]

WILD_MOVES = {
    "Pidgey": [{"name": "Tackle", "type": "Normal", "bp": 40}], "Rattata": [{"name": "Tackle", "type": "Normal", "bp": 40}],
    "Caterpie": [{"name": "Tackle", "type": "Normal", "bp": 40}], "Weedle": [{"name": "Poison Sting", "type": "Poison", "bp": 15}],
    "Metapod": [{"name": "Tackle", "type": "Normal", "bp": 40}], "Kakuna": [{"name": "Poison Sting", "type": "Poison", "bp": 15}],
    "Spearow": [{"name": "Peck", "type": "Flying", "bp": 35}], "Mankey": [{"name": "Scratch", "type": "Normal", "bp": 40}],
    "Nidoran ♀": [{"name": "Scratch", "type": "Normal", "bp": 40}], "Nidoran ♂": [{"name": "Peck", "type": "Flying", "bp": 35}],
    "Pikachu": [{"name": "Thunder Shock", "type": "Electric", "bp": 40}], "Jigglypuff": [{"name": "Sing", "type": "Normal", "bp": "Stat"}]
}

TRAINERS = {
    "Route 3": [
        {"name": "Lass Janice", "pokemon": [{"name": "Pidgey", "level": 9, "types": "Normal/Flying", "moves": [{"name": "Gust", "type": "Flying", "bp": 40}]}, {"name": "Pidgey", "level": 9, "types": "Normal/Flying", "moves": [{"name": "Gust", "type": "Flying", "bp": 40}]}]},
        {"name": "Bug Catcher Colton", "pokemon": [{"name": "Caterpie", "level": 10, "types": "Bug", "moves": [{"name": "Tackle", "type": "Normal", "bp": 40}]}, {"name": "Weedle", "level": 10, "types": "Bug/Poison", "moves": [{"name": "Poison Sting", "type": "Poison", "bp": 15}]}, {"name": "Metapod", "level": 10, "types": "Bug", "moves": [{"name": "Tackle", "type": "Normal", "bp": 40}]}]},
        {"name": "Youngster Ben", "pokemon": [{"name": "Rattata", "level": 12, "types": "Normal", "moves": [{"name": "Tackle", "type": "Normal", "bp": 40}]}, {"name": "Spearow", "level": 12, "types": "Normal/Flying", "moves": [{"name": "Peck", "type": "Flying", "bp": 35}]}]}
    ]
}

def catch_rate(wild_mon):
    max_hp, current_hp = wild_mon["max_hp"], wild_mon["hp"]
    rate = 190 if wild_mon["name"] == "Pikachu" else 255
    a = ((3 * max_hp - 2 * current_hp) * rate) / (3 * max_hp)
    return min(255, int(1048560 / math.sqrt(math.sqrt(16711680 / a))))

# ========== BATTLE VIEW ==========
class BattleView(View):
    def __init__(self, user_id, wild_mon, is_trainer=False, trainer_name=""):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.is_trainer = is_trainer
        self.trainer_name = trainer_name
        self._trainer = trainer_name
        self.trainer_pokemon = wild_mon if is_trainer else [wild_mon]
        self.current_wild_idx = 0
        self.wild = self.trainer_pokemon[0] if is_trainer else wild_mon
        self.active_idx = first_alive()
        self.active = save["party"][self.active_idx] if self.active_idx is not None else None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your battle.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.user_id in active_battles: del active_battles[self.user_id]

    def build_embed(self):
        w, a = self.wild, self.active
        if a is None: return discord.Embed(title="⚔️ Battle!", description="All your Pokémon have fainted!", color=0xFF0000)
        shiny = "✨ " if w.get("shiny") else ""
        lines = [f"{shiny}**{w['name']}**  Lv.{w['level']}  {w['types']}", hp_bar(w['hp'], w['max_hp']), "", f"**{a['name']}**  Lv.{a['level']}  {a['types']}", hp_bar(a['hp'], a['max_hp']), ""]
        for i, move in enumerate(a["moves"], 1):
            bp = f"{move['bp']} BP" if isinstance(move['bp'], int) else move['bp']
            lines.append(f"{i}. {move['name']}  {move['type']}  {bp}  {move['pp']}/{move['max_pp']} PP")
        return discord.Embed(title="⚔️ Battle!", description="\n".join(lines), color=0x50C878)

    def build_buttons(self):
        self.clear_items()
        if self.active is None: return
        for i, move in enumerate(self.active["moves"], 1):
            self.add_item(Button(label=f"{i}. {move['name']}", row=0, disabled=(move["pp"] <= 0)))
        self.children[-1].callback = self.make_move_callback(i) if len(self.children) > 0 else None
        self.clear_items()
        for i, move in enumerate(self.active["moves"], 1):
            btn = Button(label=f"{i}. {move['name']}", row=0, disabled=(move["pp"] <= 0))
            btn.callback = self.make_move_callback(i)
            self.add_item(btn)
        if not self.is_trainer:
            btn2 = Button(label="🎯 Catch", row=1, style=discord.ButtonStyle.success, disabled=(save["inventory"]["poke_balls"] <= 0))
            btn2.callback = self.catch_callback
            self.add_item(btn2)
        btn3 = Button(label="🏃 Run", row=1, style=discord.ButtonStyle.danger)
        btn3.callback = self.run_callback
        self.add_item(btn3)

    def make_move_callback(self, move_idx):
        async def callback(interaction: discord.Interaction):
            if self.active is None: await interaction.response.edit_message(content="No Pokémon!", embed=None, view=None); return
            active, wild, move = self.active, self.wild, self.active["moves"][move_idx - 1]
            if move["pp"] <= 0: await interaction.response.send_message("No PP left!", ephemeral=True); return
            move["pp"] -= 1
            bp = move["bp"] if isinstance(move["bp"], int) else 40
            mult = type_multiplier(move["type"], wild["types"])
            damage = max(1, int((active["level"] * bp / 30) * mult * random.uniform(0.85, 1.0)))
            wild["hp"] = max(0, wild["hp"] - damage)
            lines = [f"**{active['name']}** used **{move['name']}**!"]
            if mult == 0: lines.append(f"It doesn't affect {wild['name']}...")
            elif mult < 1: lines.append("It's not very effective...")
            elif mult > 1: lines.append("It's super effective!")
            if wild["hp"] <= 0:
                exp_gain = wild["level"] * 15; active["exp"] += exp_gain
                lines.append(f"Wild {wild['name']} fainted!"); lines.append(f"**{active['name']}** gained {exp_gain} EXP!")
                lines.append(level_up(active))
                if self.is_trainer:
                    self.current_wild_idx += 1
                    if self.current_wild_idx < len(self.trainer_pokemon):
                        self.wild = self.trainer_pokemon[self.current_wild_idx]
                        lines.append(f"{self.trainer_name} sent out **{self.wild['name']}**!")
                        self.build_buttons(); await interaction.response.edit_message(content="\n".join(lines), embed=self.build_embed(), view=self); save_game(save); return
                    else:
                        lines.append(f"🏆 You defeated {self.trainer_name}!"); save["money"] += 200; lines.append("Gained ₽200!")
                        if self._trainer == "Forrest":
                            save["story_flags"]["brock_defeated"] = True
                            save["badges"].append("Boulder Badge")
                            save["money"] += 800
                            lines.append("🏅 **Boulder Badge** obtained!"); lines.append("✅ Gained ₽1,000 total!")
                            save_game(save)
                            await interaction.followup.send("🏆 **Forrest was defeated!**\n\n\"You're the real deal. Brock was right.\"\n\n✅ **Boulder Badge** obtained!\n✅ Gained ₽1,000!", ephemeral=False)
                if self.user_id in active_battles: del active_battles[self.user_id]
                save_game(save); await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None); return
            w_move = random.choice(WILD_MOVES.get(wild["name"], [{"name": "Tackle", "type": "Normal", "bp": 40}]))
            w_mult = type_multiplier(w_move["type"], active["types"])
            if w_move["bp"] == "Stat":
                lines.append(f"Wild **{wild['name']}** used **{w_move['name']}**!")
                if w_move["name"] == "Sing": lines.append(f"**{active['name']}** fell asleep!")
            elif w_mult == 0: lines.append(f"Wild **{wild['name']}** used **{w_move['name']}**!\nIt doesn't affect **{active['name']}**...")
            else:
                w_damage = max(1, int((wild["level"] * w_move["bp"] / 30) * w_mult * random.uniform(0.85, 1.0)))
                active["hp"] = max(0, active["hp"] - w_damage)
                lines.append(f"Wild **{wild['name']}** used **{w_move['name']}**!")
                if w_mult < 1: lines.append("It's not very effective...")
                elif w_mult > 1: lines.append("It's super effective!")
            if active["hp"] <= 0:
                lines.append(f"**{active['name']}** fainted!")
                next_idx = first_alive()
                if next_idx is not None: self.active_idx = next_idx; self.active = save["party"][next_idx]; lines.append(f"Go! **{self.active['name']}**!")
                else: lines.append("All your Pokémon have fainted!"); del active_battles[self.user_id]; save_game(save); await interaction.response.edit_message(content="\n".join(lines), embed=None, view=None); return
            self.build_buttons(); await interaction.response.edit_message(content="\n".join(lines), embed=self.build_embed(), view=self)
        return callback

    async def catch_callback(self, interaction: discord.Interaction):
        if save["inventory"]["poke_balls"] <= 0: await interaction.response.send_message("No Poké Balls!", ephemeral=True); return
        save["inventory"]["poke_balls"] -= 1
        rate = catch_rate(self.wild); shakes = sum(1 for _ in range(3) if random.randint(0, 255) < rate)
        shake_text = ["...", "......", "........."]
        if shakes == 3:
            msg = f"🟢 You threw a Poké Ball!\n{shake_text[0]}\n{shake_text[1]}\n{shake_text[2]}\n**Gotcha! {self.wild['name']} was caught!**"
            new_mon = {"name": self.wild["name"], "level": self.wild["level"], "hp": self.wild["max_hp"], "max_hp": self.wild["max_hp"], "exp": 0, "nature": random.choice(NATURES), "types": self.wild["types"], "shiny": self.wild.get("shiny", False), "ability": "Standard", "held": None, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40, "pp": 35, "max_pp": 35}]}
            if len(save["party"]) < 6: save["party"].append(new_mon); msg += f"\n{self.wild['name']} added to your party!"
            else: save["box"].append(new_mon); msg += f"\n{self.wild['name']} sent to PC box!"
            if self.user_id in active_battles: del active_battles[self.user_id]
            save_game(save); await interaction.response.edit_message(content=msg, embed=None, view=None)
        else:
            msg = f"🔴 You threw a Poké Ball!\n" + "\n".join(shake_text[:shakes]) + "\nOh no! It broke free!"
            self.build_buttons(); await interaction.response.edit_message(content=msg, embed=self.build_embed(), view=self)

    async def run_callback(self, interaction: discord.Interaction):
        if self.is_trainer: await interaction.response.send_message("Can't run!", ephemeral=True); return
        if self.user_id in active_battles: del active_battles[self.user_id]
        await interaction.response.edit_message(content="Got away safely!", embed=None, view=None)

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    await bot.tree.sync(); print(f"Online as {bot.user}")
# ========== TITLE SCREEN ==========
@bot.tree.command(name="start", description="Open the title screen")
async def start(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ POKÉMON: RIFT ⚡",
        description=(
            "*A darker journey awaits.*\n\n"
            "**Your childhood friend is missing.**\n"
            "**An impossible Pokémon hatched from her final egg.**\n"
            "**The League won't help. The wilderness is lethal.**\n"
            "**And the clues point toward something ancient — something sealed.**\n\n"
            "*The Rift is opening. Are you ready?*"
        ),
        color=0x4B0082
    )
    class TitleView(View):
        def __init__(self):
            super().__init__(timeout=600)
        @discord.ui.button(label="🆕 New Game", style=discord.ButtonStyle.success, row=0)
        async def new_game(self, btn_i, btn):
            if os.path.exists(SAVE_FILE):
                class ConfirmView(View):
                    def __init__(self): super().__init__(timeout=60)
                    @discord.ui.button(label="Yes, start fresh", style=discord.ButtonStyle.danger)
                    async def confirm(self, ci, cb):
                        os.remove(SAVE_FILE)
                        global save; save = DEFAULT_SAVE.copy(); save_game(save)
                        await start_game_intro(ci)
                    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
                    async def cancel(self, ci, cb): await ci.response.edit_message(embed=embed, view=TitleView())
                await btn_i.response.edit_message(content="⚠️ A save file exists. Overwrite?", embed=None, view=ConfirmView())
            else:
                global save; save = DEFAULT_SAVE.copy(); save_game(save)
                await start_game_intro(btn_i)
        @discord.ui.button(label="💾 Continue", style=discord.ButtonStyle.primary, row=0)
        async def load_game(self, btn_i, btn):
            if not os.path.exists(SAVE_FILE): await btn_i.response.send_message("No save file found.", ephemeral=True); return
            global save; save = load_save()
            embed2 = discord.Embed(title="Game Loaded", description=f"**Location:** {save['location']}\n**Money:** ₽{save['money']}\n**Badges:** {len(save['badges'])}\n**Party:** {len(save['party'])} Pokémon\n\nUse **/menu** to play or **/story** to continue.", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed2, view=None)
    await interaction.response.send_message(embed=embed, view=TitleView())

async def start_game_intro(interaction):
    embed1 = discord.Embed(title="Pallet Town — Late Afternoon", description="*The sea glitters. Pidgey call from the rooftops. You've lived here your whole life.*\n\n*You are GR22N. Your friends became legends. You never became a trainer. But Leaf is missing — and you're going to find her.*\n\n*You're in Daisy Oak's bedroom. She's beside you, tracing the scar on your shoulder.*", color=0x4B0082)
    class IntroView(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="Go to the window", style=discord.ButtonStyle.primary)
        async def to_window(self, btn_i, btn):
            self.clear_items()
            btn1 = Button(label="Go downstairs", style=discord.ButtonStyle.primary)
            btn1.callback = self.go_downstairs; self.add_item(btn1)
            embed2 = discord.Embed(title="Daisy's Room", description="*An Aerodactyl stands in the ruined garden. Blood on its beak. The man dismounting is BLUE.*\n\n**DAISY:** \"Who is it?\"", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed2, view=self)
        async def go_downstairs(self, btn_i):
            embed3 = discord.Embed(title="Oak's Living Room", description="**BLUE:** \"Red's missing. Leaf's been off-grid for six months.\"\n\n*He notices you.*\n\n**BLUE:** \"You've never thrown a Poké Ball. Stay here. Let the real trainers handle this.\"\n\n*He leaves. Oak says nothing.*", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed3, view=DaisyCharmView())
    await interaction.response.edit_message(embed=embed1, view=IntroView())

class DaisyCharmView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Return to Daisy", style=discord.ButtonStyle.primary)
    async def back_to_daisy(self, btn_i, btn):
        embed = discord.Embed(title="Daisy's Gift", description="**DAISY:** \"You're going after her.\"\n\n*She presses a warm, iridescent charm into your palm.*\n\n**DAISY:** \"It was my mother's. It brought luck. Just... don't die.\"\n\n✅ **Shiny Charm** obtained!", color=0x4B0082)
        save["story_flags"]["daisy_oak_gave_shiny_charm"] = True; save_game(save)
        await btn_i.response.edit_message(embed=embed, view=LeafsHouseIntroView())

class LeafsHouseIntroView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Go to Leaf's house", style=discord.ButtonStyle.primary)
    async def to_leafs(self, btn_i, btn):
        embed = discord.Embed(title="Leaf's House — Evening", description="*The study is chaos — maps, notes, a corkboard with fifteen missing persons connected to Mt. Coronet. Words repeat: RIFT. HISUI. VANE.*\n\n*In the corner, an incubator hums.*\n\n*You reach out.*", color=0x4B0082)
        await btn_i.response.edit_message(embed=embed, view=EggHatchIntroView())

class EggHatchIntroView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="🥚 Touch the egg", style=discord.ButtonStyle.success)
    async def hatch(self, btn_i, btn):
        save["story_flags"]["leaf_egg_hatched"] = True; save["story_flags"]["knows_dr_vane_name"] = True
        save["story_flags"]["blue_mocked_and_left"] = True; save_game(save)
        embed = discord.Embed(title="The Egg Hatches", description="*The shell splits. A fox — white fur, blue spectral wisps, ancient yellow eyes — tumbles into your hands.*\n\n**Shiny Hisuian Zorua.** A Pokémon that doesn't exist in any Pokédex.\n\n*Leaf's last note:*\n\"Don't trust the League. Hisui is real. The Rift is opening. Find me if you can. —L\"\n\n✅ **Shiny Hisuian Zorua** joined!\n✅ **Objective: Find Leaf**\n\nUse **/menu** to play. Use **/story** to continue.", color=0x4B0082)
        await btn_i.response.edit_message(embed=embed, view=None)

# ========== STORY COMMANDS ==========
@bot.tree.command(name="story", description="Continue the main story")
async def story(interaction: discord.Interaction):
    flags = save["story_flags"]; loc = save["location"]
    if loc == "Viridian Forest" and not flags.get("met_aurora"):
        await aurora_scene(interaction)
    elif loc == "Pewter City" and not flags.get("brock_defeated"):
        await brock_gym_challenge(interaction)
    elif not flags.get("brock_defeated"):
        await interaction.response.send_message("Head to Pewter City. The Gym awaits.", ephemeral=True)
    else:
        await interaction.response.send_message("All current story content complete. More coming soon!", ephemeral=True)

async def aurora_scene(interaction):
    embed = discord.Embed(title="Viridian Forest — Night", description="*A light flickers. A woman crouches by a fallen tree — silver-blue hair, sharp green eyes. A Pelipper mists the air with rain. Her white shirt is soaked.*\n\n**???:** \"You're either very brave or very stupid. Which is it?\"\n\n**???:** \"I'm Aurora. Investigative journalist.\"", color=0x2E8B57)
    class AV(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="...", style=discord.ButtonStyle.primary)
        async def talk(self, btn_i, btn):
            save["story_flags"]["met_aurora"] = True; save["inventory"]["key_items"] = save["inventory"].get("key_items", []) + ["Aurora's Radio Frequency"]; save_game(save)
            embed2 = discord.Embed(title="Aurora Voss — Journalist", description="**AURORA:** \"That's a Hisuian Zorua. Those don't exist anymore.\"\n\n*You tell her about Leaf.*\n\n**AURORA:** \"Leaf was my source. For five years.\"\n\n*She presses a radio into your hand.*\n\n**AURORA:** \"If you find anything, call me. Try not to die.\"\n\n✅ **Aurora's Radio Frequency** obtained!", color=0x2E8B57)
            await btn_i.response.edit_message(embed=embed2, view=None)
    await interaction.response.send_message(embed=embed, view=AV())

async def brock_gym_challenge(interaction):
    first = save["story_flags"].get("brock_first_attempt", True)
    if first:
        embed = discord.Embed(title="Pewter Gym — Forrest", description="**FORREST:** \"GR22N, right? My brother told me about you. Doubles. Six-on-six. No items. Let's rock.\"", color=0xB8860B)
    else:
        embed = discord.Embed(title="Pewter Gym — Forrest", description="**FORREST:** \"Back for more? Let's go.\"", color=0xB8860B)
    class GV(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="⚔️ Challenge Forrest", style=discord.ButtonStyle.danger)
        async def fight(self, btn_i, btn):
            save["story_flags"]["brock_first_attempt"] = False; save_game(save)
            mons = [
                {"name": "Geodude", "level": 12, "types": "Rock/Ground", "hp": 40, "max_hp": 40, "moves": [{"name": "Rock Throw", "type": "Rock", "bp": 50}]},
                {"name": "Onix", "level": 14, "types": "Rock/Ground", "hp": 50, "max_hp": 50, "moves": [{"name": "Rock Slide", "type": "Rock", "bp": 75}]},
                {"name": "Geodude", "level": 12, "types": "Rock/Ground", "hp": 40, "max_hp": 40, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40}]},
                {"name": "Kabuto", "level": 13, "types": "Rock/Water", "hp": 42, "max_hp": 42, "moves": [{"name": "Aqua Jet", "type": "Water", "bp": 40}]},
                {"name": "Cranidos", "level": 14, "types": "Rock", "hp": 48, "max_hp": 48, "moves": [{"name": "Headbutt", "type": "Normal", "bp": 70}]},
                {"name": "Onix", "level": 15, "types": "Rock/Ground", "hp": 55, "max_hp": 55, "moves": [{"name": "Rock Slide", "type": "Rock", "bp": 75}]}
            ]
            view = BattleView(btn_i.user.id, mons, is_trainer=True, trainer_name="Forrest")
            active_battles[btn_i.user.id] = view; view.build_buttons()
            await btn_i.response.edit_message(content="⚔️ **Gym Leader Forrest** challenges you!", embed=view.build_embed(), view=view)
    await interaction.response.send_message(embed=embed, view=GV())
# ========== MAIN MENU ==========
@bot.tree.command(name="menu", description="Open the main game menu")
async def menu(interaction: discord.Interaction):
    class MainMenu(View):
        def __init__(self):
            super().__init__(timeout=300)
        @discord.ui.button(label="🎒 Party", style=discord.ButtonStyle.primary, row=0)
        async def pty(self2, s, b): await s.response.send_message(party_display(), ephemeral=True)
        @discord.ui.button(label="🎒 Bag", style=discord.ButtonStyle.primary, row=0)
        async def bag(self2, s, b):
            inv = save["inventory"]
            await s.response.send_message(f"**Bag**\nPoké Balls: {inv['poke_balls']}\nPotions: {inv['potions']}\nAntidotes: {inv['antidotes']}\nMoney: ₽{save['money']}\nLocation: {save['location']}", ephemeral=True)
        @discord.ui.button(label="🔍 Explore", style=discord.ButtonStyle.success, row=1)
        async def expl(self2, s, b):
            await s.response.defer(); loc = save["location"]
            table = ENCOUNTERS.get(loc, [])
            if not table: await s.followup.send("No wild Pokémon here.", ephemeral=True); return
            if s.user.id in active_battles: await s.followup.send("Already in a battle!", ephemeral=True); return
            if loc in TRAINERS and random.random() < 0.25:
                trainer = random.choice(TRAINERS[loc])
                mons = [{"name": t["name"], "level": t["level"], "types": t["types"], "hp": 15 + t["level"] * 3, "max_hp": 15 + t["level"] * 3, "moves": t["moves"]} for t in trainer["pokemon"]]
                view = BattleView(s.user.id, mons, is_trainer=True, trainer_name=trainer["name"])
                active_battles[s.user.id] = view; view.build_buttons()
                await s.followup.send(f"🧢 **{trainer['name']}** wants to battle!", embed=view.build_embed(), view=view); return
            encounter = random.choice(table); level = random.randint(*encounter["level"])
            shiny = random.randint(1, 4096) == 1
            wild_mon = {"name": encounter["name"], "level": level, "types": encounter["types"], "hp": 15 + level * 3, "max_hp": 15 + level * 3, "shiny": shiny}
            view = BattleView(s.user.id, wild_mon); active_battles[s.user.id] = view; view.build_buttons()
            await s.followup.send(f"{'✨ ' if shiny else ''}Wild **{encounter['name']}** appeared! Lv.{level}", embed=view.build_embed(), view=view)
        @discord.ui.button(label="🗺️ Map", style=discord.ButtonStyle.secondary, row=1)
        async def mp(self2, s, b):
            loc = save["location"]; connections = LOCATIONS.get(loc, {})
            lines = [f"**📍 {loc}**\n"]
            for d, dest in connections.items(): lines.append(f"**{d}** → {dest}")
            if not connections: lines.append("Nowhere to go.")
            class MV(View):
                def __init__(self):
                    super().__init__(timeout=60)
                    for d, dest in connections.items():
                        btn = Button(label=f"{d} → {dest}", style=discord.ButtonStyle.secondary)
                        btn.callback = (lambda d2=d, d3=dest: (lambda mi: (setattr(save, "location", d3), save_game(save), mi.response.send_message(f"Traveled {d2} to **{d3}**."))[2])())
                        self.add_item(btn)
            await s.response.send_message("\n".join(lines), view=MV() if connections else None, ephemeral=True)
        @discord.ui.button(label="🏥 Heal", style=discord.ButtonStyle.danger, row=2)
        async def hl(self2, s, b):
            if save["location"] not in ["Pallet Town", "Viridian City", "Pewter City"]: await s.response.send_message("Need to be in a city!", ephemeral=True); return
            for mon in save["party"]: mon["hp"] = mon["max_hp"]; [move.update({"pp": move["max_pp"]}) for move in mon["moves"]]
            save_game(save); await s.response.send_message("✅ Team fully healed!", ephemeral=True)
        @discord.ui.button(label="🛒 Shop", style=discord.ButtonStyle.success, row=2)
        async def shp(self2, s, b):
            if save["location"] not in ["Viridian City", "Pewter City"]: await s.response.send_message("No Poké Mart here.", ephemeral=True); return
            class SV(View):
                def __init__(self): super().__init__(timeout=60)
                @discord.ui.button(label="Poké Ball - ₽200", style=discord.ButtonStyle.primary)
                async def pb(self3, ss, bb):
                    if save["money"] >= 200: save["money"] -= 200; save["inventory"]["poke_balls"] += 1; save_game(save); await ss.response.send_message("Bought 1 Poké Ball!", ephemeral=True)
                    else: await ss.response.send_message("Not enough money!", ephemeral=True)
                @discord.ui.button(label="Potion - ₽300", style=discord.ButtonStyle.primary)
                async def pot(self3, ss, bb):
                    if save["money"] >= 300: save["money"] -= 300; save["inventory"]["potions"] += 1; save_game(save); await ss.response.send_message("Bought 1 Potion!", ephemeral=True)
                    else: await ss.response.send_message("Not enough money!", ephemeral=True)
                @discord.ui.button(label="Antidote - ₽100", style=discord.ButtonStyle.secondary)
                async def ant(self3, ss, bb):
                    if save["money"] >= 100: save["money"] -= 100; save["inventory"]["antidotes"] += 1; save_game(save); await ss.response.send_message("Bought 1 Antidote!", ephemeral=True)
                    else: await ss.response.send_message("Not enough money!", ephemeral=True)
            await s.response.send_message(f"**Poké Mart** — ₽{save['money']}", view=SV(), ephemeral=True)
        @discord.ui.button(label="🔄 Switch Lead", style=discord.ButtonStyle.secondary, row=3)
        async def sw(self2, s, b):
            options = [discord.SelectOption(label=f"{i+1}. {m['name']} Lv.{m['level']}", value=str(i)) for i, m in enumerate(save["party"])]
            class S(Select):
                def __init__(self): super().__init__(placeholder="Choose lead...", options=options)
                async def callback(self, si):
                    idx = int(self.values[0]); save["party"].insert(0, save["party"].pop(idx)); save_game(save)
                    await si.response.send_message(f"**{save['party'][0]['name']}** is now in the lead!", ephemeral=True)
            v = View(timeout=60); v.add_item(S()); await s.response.send_message("Choose your lead:", view=v, ephemeral=True)
        @discord.ui.button(label="📦 PC Box", style=discord.ButtonStyle.secondary, row=3)
        async def bx(self2, s, b):
            box = save.get("box", [])
            if not box: await s.response.send_message("PC box is empty.", ephemeral=True); return
            lines = [f"**PC Box ({len(box)} Pokémon)**\n"]
            for i, m in enumerate(box, 1): lines.append(f"{i}. {'✨ ' if m.get('shiny') else ''}{m['name']} Lv.{m['level']} {m['types']}")
            await s.response.send_message("\n".join(lines), ephemeral=True)
    await interaction.response.send_message("**📋 MAIN MENU**", view=MainMenu(), ephemeral=True)

# ========== TITLE SCREEN ==========
@bot.tree.command(name="start", description="Open the title screen")
async def start(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ POKÉMON: RIFT ⚡",
        description=(
            "*A darker journey awaits.*\n\n"
            "**Your childhood friend is missing.**\n"
            "**An impossible Pokémon hatched from her final egg.**\n"
            "**The League won't help. The wilderness is lethal.**\n"
            "**And the clues point toward something ancient — something sealed.**\n\n"
            "*The Rift is opening. Are you ready?*"
        ),
        color=0x4B0082
    )
    embed.set_footer(text="Version 1.0 — Pokémon: Rift")
    class TitleView(View):
        def __init__(self):
            super().__init__(timeout=600)
        @discord.ui.button(label="🆕 New Game", style=discord.ButtonStyle.success, row=0)
        async def new_game(self, btn_i, btn):
            if os.path.exists(SAVE_FILE):
                class ConfirmView(View):
                    def __init__(self): super().__init__(timeout=60)
                    @discord.ui.button(label="Yes, start fresh", style=discord.ButtonStyle.danger)
                    async def confirm(self, ci, cb):
                        os.remove(SAVE_FILE)
                        global save; save = DEFAULT_SAVE.copy(); save_game(save)
                        await start_game_intro(ci)
                    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
                    async def cancel(self, ci, cb): await ci.response.edit_message(embed=embed, view=TitleView())
                await btn_i.response.edit_message(content="⚠️ A save file exists. Overwrite?", embed=None, view=ConfirmView())
            else:
                global save; save = DEFAULT_SAVE.copy(); save_game(save)
                await start_game_intro(btn_i)
        @discord.ui.button(label="💾 Continue", style=discord.ButtonStyle.primary, row=0)
        async def load_game(self, btn_i, btn):
            if not os.path.exists(SAVE_FILE): await btn_i.response.send_message("No save file found.", ephemeral=True); return
            global save; save = load_save()
            embed2 = discord.Embed(title="Game Loaded", description=f"**Location:** {save['location']}\n**Money:** ₽{save['money']}\n**Badges:** {len(save['badges'])}\n**Party:** {len(save['party'])} Pokémon\n\nUse **/menu** to play or **/story** to continue.", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed2, view=None)
        @discord.ui.button(label="❓ How to Play", style=discord.ButtonStyle.secondary, row=1)
        async def how_to(self, btn_i, btn):
            help_embed = discord.Embed(title="How to Play", description="**/menu** — Main game menu\n**/story** — Continue the story\n**/start** — Title screen\n\nUse the Map in /menu to travel.\nUse Explore to find wild Pokémon.\nUse Heal in cities to restore your team.\nUse Shop to buy items.\n\n*This world is dangerous. Your Pokémon can die.*", color=0x4B0082)
            await btn_i.response.send_message(embed=help_embed, ephemeral=True)
    await interaction.response.send_message(embed=embed, view=TitleView())

async def start_game_intro(interaction):
    embed1 = discord.Embed(title="Pallet Town — Late Afternoon", description="*The sea glitters. Pidgey call from the rooftops. You've lived here your whole life.*\n\n*You are GR22N. Your friends became legends. You never became a trainer. But Leaf is missing — and you're going to find her.*\n\n*You're in Daisy Oak's bedroom. She's beside you, tracing the scar on your shoulder.*", color=0x4B0082)
    class IntroView(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="Go to the window", style=discord.ButtonStyle.primary)
        async def to_window(self, btn_i, btn):
            self.clear_items()
            btn1 = Button(label="Go downstairs", style=discord.ButtonStyle.primary)
            btn1.callback = self.go_downstairs; self.add_item(btn1)
            embed2 = discord.Embed(title="Daisy's Room", description="*An Aerodactyl stands in the ruined garden. Blood on its beak. The man dismounting is BLUE.*\n\n**DAISY:** \"Who is it?\"", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed2, view=self)
        async def go_downstairs(self, btn_i):
            embed3 = discord.Embed(title="Oak's Living Room", description="**BLUE:** \"Red's missing. Leaf's been off-grid for six months.\"\n\n*He notices you.*\n\n**BLUE:** \"You've never thrown a Poké Ball. Stay here. Let the real trainers handle this.\"\n\n*He leaves. Oak says nothing.*", color=0x4B0082)
            await btn_i.response.edit_message(embed=embed3, view=DaisyCharmView())
    await interaction.response.edit_message(embed=embed1, view=IntroView())

class DaisyCharmView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Return to Daisy", style=discord.ButtonStyle.primary)
    async def back_to_daisy(self, btn_i, btn):
        embed = discord.Embed(title="Daisy's Gift", description="**DAISY:** \"You're going after her.\"\n\n*She presses a warm, iridescent charm into your palm.*\n\n**DAISY:** \"It was my mother's. It brought luck. Just... don't die.\"\n\n✅ **Shiny Charm** obtained!", color=0x4B0082)
        save["story_flags"]["daisy_oak_gave_shiny_charm"] = True; save_game(save)
        await btn_i.response.edit_message(embed=embed, view=LeafsHouseIntroView())

class LeafsHouseIntroView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="Go to Leaf's house", style=discord.ButtonStyle.primary)
    async def to_leafs(self, btn_i, btn):
        embed = discord.Embed(title="Leaf's House — Evening", description="*The study is chaos — maps, notes, a corkboard with fifteen missing persons connected to Mt. Coronet. Words repeat: RIFT. HISUI. VANE.*\n\n*In the corner, an incubator hums.*\n\n*You reach out.*", color=0x4B0082)
        await btn_i.response.edit_message(embed=embed, view=EggHatchIntroView())

class EggHatchIntroView(View):
    def __init__(self): super().__init__(timeout=300)
    @discord.ui.button(label="🥚 Touch the egg", style=discord.ButtonStyle.success)
    async def hatch(self, btn_i, btn):
        save["story_flags"]["leaf_egg_hatched"] = True; save["story_flags"]["knows_dr_vane_name"] = True
        save["story_flags"]["blue_mocked_and_left"] = True; save_game(save)
        embed = discord.Embed(title="The Egg Hatches", description="*The shell splits. A fox — white fur, blue spectral wisps, ancient yellow eyes — tumbles into your hands.*\n\n**Shiny Hisuian Zorua.** A Pokémon that doesn't exist in any Pokédex.\n\n*Leaf's last note:*\n\"Don't trust the League. Hisui is real. The Rift is opening. Find me if you can. —L\"\n\n✅ **Shiny Hisuian Zorua** joined!\n✅ **Objective: Find Leaf**\n\nUse **/menu** to play. Use **/story** to continue.", color=0x4B0082)
        await btn_i.response.edit_message(embed=embed, view=None)

# ========== STORY COMMANDS ==========
@bot.tree.command(name="story", description="Continue the main story")
async def story(interaction: discord.Interaction):
    flags = save["story_flags"]; loc = save["location"]
    if loc == "Viridian Forest" and not flags.get("met_aurora"):
        await aurora_scene(interaction)
    elif loc == "Pewter City" and not flags.get("brock_defeated"):
        await brock_gym_challenge(interaction)
    elif not flags.get("brock_defeated"):
        await interaction.response.send_message("Head to Pewter City. The Gym awaits.", ephemeral=True)
    else:
        await interaction.response.send_message("All current story content complete. More coming soon!", ephemeral=True)

async def aurora_scene(interaction):
    embed = discord.Embed(title="Viridian Forest — Night", description="*A light flickers. A woman crouches by a fallen tree — silver-blue hair, sharp green eyes. A Pelipper mists the air with rain. Her white shirt is soaked.*\n\n**???:** \"You're either very brave or very stupid. Which is it?\"\n\n**???:** \"I'm Aurora. Investigative journalist.\"", color=0x2E8B57)
    class AV(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="...", style=discord.ButtonStyle.primary)
        async def talk(self, btn_i, btn):
            save["story_flags"]["met_aurora"] = True; save["inventory"]["key_items"] = save["inventory"].get("key_items", []) + ["Aurora's Radio Frequency"]; save_game(save)
            embed2 = discord.Embed(title="Aurora Voss — Journalist", description="**AURORA:** \"That's a Hisuian Zorua. Those don't exist anymore.\"\n\n*You tell her about Leaf.*\n\n**AURORA:** \"Leaf was my source. For five years.\"\n\n*She presses a radio into your hand.*\n\n**AURORA:** \"If you find anything, call me. Try not to die.\"\n\n✅ **Aurora's Radio Frequency** obtained!", color=0x2E8B57)
            await btn_i.response.edit_message(embed=embed2, view=None)
    await interaction.response.send_message(embed=embed, view=AV())

async def brock_gym_challenge(interaction):
    first = save["story_flags"].get("brock_first_attempt", True)
    if first:
        embed = discord.Embed(title="Pewter Gym — Forrest", description="**FORREST:** \"GR22N, right? My brother told me about you. Doubles. Six-on-six. No items. Let's rock.\"", color=0xB8860B)
    else:
        embed = discord.Embed(title="Pewter Gym — Forrest", description="**FORREST:** \"Back for more? Let's go.\"", color=0xB8860B)
    class GV(View):
        def __init__(self): super().__init__(timeout=300)
        @discord.ui.button(label="⚔️ Challenge Forrest", style=discord.ButtonStyle.danger)
        async def fight(self, btn_i, btn):
            save["story_flags"]["brock_first_attempt"] = False; save_game(save)
            mons = [
                {"name": "Geodude", "level": 12, "types": "Rock/Ground", "hp": 40, "max_hp": 40, "moves": [{"name": "Rock Throw", "type": "Rock", "bp": 50}]},
                {"name": "Onix", "level": 14, "types": "Rock/Ground", "hp": 50, "max_hp": 50, "moves": [{"name": "Rock Slide", "type": "Rock", "bp": 75}]},
                {"name": "Geodude", "level": 12, "types": "Rock/Ground", "hp": 40, "max_hp": 40, "moves": [{"name": "Tackle", "type": "Normal", "bp": 40}]},
                {"name": "Kabuto", "level": 13, "types": "Rock/Water", "hp": 42, "max_hp": 42, "moves": [{"name": "Aqua Jet", "type": "Water", "bp": 40}]},
                {"name": "Cranidos", "level": 14, "types": "Rock", "hp": 48, "max_hp": 48, "moves": [{"name": "Headbutt", "type": "Normal", "bp": 70}]},
                {"name": "Onix", "level": 15, "types": "Rock/Ground", "hp": 55, "max_hp": 55, "moves": [{"name": "Rock Slide", "type": "Rock", "bp": 75}]}
            ]
            view = BattleView(btn_i.user.id, mons, is_trainer=True, trainer_name="Forrest")
            active_battles[btn_i.user.id] = view; view.build_buttons()
            await btn_i.response.edit_message(content="⚔️ **Gym Leader Forrest** challenges you!", embed=view.build_embed(), view=view)
    await interaction.response.send_message(embed=embed, view=GV())
@bot.tree.command(name="reset_commands", description="Force sync all commands")
async def reset_commands(interaction: discord.Interaction):
    await interaction.response.send_message("Resetting...", ephemeral=True)
# ========== RUN ==========
bot.run(os.environ["DISCORD_TOKEN"])
