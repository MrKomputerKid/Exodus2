import json
import random
import discord
from discord import app_commands

# Load jokes from JSON file
def load_jokes():
    try:
        with open('jokes.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"jokes": []}

# Save jokes to JSON file
def save_jokes(jokes):
    with open('jokes.json', 'w') as f:
        json.dump(jokes, f, indent=4)

# Get a random joke
def get_random_joke():
    jokes = load_jokes()
    if jokes["jokes"]:
        return random.choice(jokes["jokes"])
    return "No jokes available."

# Add a new joke
def add_joke(setup, punchline):
    jokes = load_jokes()
    jokes["jokes"].append({"setup": setup, "punchline": punchline})
    save_jokes(jokes)

@app_commands.command(name="joke", description="Get a random joke")
async def joke(interaction: discord.Interaction):
    joke = get_random_joke()
    embed = discord.Embed(title="Here's a joke for you!", color=discord.Color.blurple())
    embed.add_field(name="Setup", value=joke["setup"], inline=False)
    embed.add_field(name="Punchline", value=joke["punchline"], inline=False)
    await interaction.response.send_message(embed=embed)

@app_commands.command(name="addjoke", description="Add a new joke")
async def add_joke_command(interaction: discord.Interaction, setup: str, punchline: str):
    add_joke(setup, punchline)
    await interaction.response.send_message("Joke added successfully!", ephemeral=True)