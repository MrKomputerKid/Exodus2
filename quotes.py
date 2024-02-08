import discord
import random
import logging
from discord.ext import commands, app_commands
import json

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Function to load quotes from the specified database file
def load_quotes(database):
    try:
        with open(database, 'r', encoding='utf-8') as file:
            quotes = json.load(file)
        return quotes
    except FileNotFoundError:
        return None

# Quote command. Pulls from the specified database
@tree.command(name='quote', description='Get a random quote from the specified database')
async def quote(interaction, database: str):
    embed = discord.Embed(title="Quote", color=discord.Color.blurple())
    if database in ['quotes']:
        quotes = load_quotes(f"{database}.json")  # Adjust the database file names as per your actual filenames
        if quotes:
            random_quote = random.choice(quotes)
            embed.add_field(name='', value=f"```{random_quote}```", inline=True)
        else:
            embed.add_field(name='Error', value=f"No quotes found in the {database} database.", inline=True)
    else:
        embed.add_field(name='Error', value="Invalid database specified. Available options: ai, techtalk, bash-org.", inline=True)
    
    await interaction.response.send_message(embed=embed)

# Run the client
client.run('YOUR_DISCORD_BOT_TOKEN')
