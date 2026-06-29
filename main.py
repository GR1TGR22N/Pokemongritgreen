import discord
from discord.ext import commands
import json
import os
import asyncio
import random

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== SAVE DATA ==========
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

def hp_bar(current, maximum):
    pct = current / maximum
    filled = round(pct * 4)
    return f"HP {'█' * filled}{'░' * (4 - filled)} {int(pct * 100)}%"

# ========== BOT EVENTS ==========
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Online as {bot.user}")

# ========== SLASH COMMANDS ==========
@bot.tree.command(name="party", description="View your Pokémon team")
async def party(interaction: discord.Interaction):
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
    await interaction.response.send_message("\n".join(lines))

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

# ========== RUN BOT ==========
bot.run(os.environ["DISCORD_TOKEN"])
