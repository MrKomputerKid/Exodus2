import discord
import random
import logging
from discord import app_commands
import json

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Function to load quotes from the quotes.json file
def load_quotes():
    try:
        with open('quotes.json', 'r', encoding='utf-8') as file:
            quotes_data = json.load(file)
        return quotes_data
    except FileNotFoundError:
        print("Error: File 'quotes.json' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file 'quotes.json': {e}")
        return None

# Quote command. Pulls a random quote from the quotes.json file
@tree.command(name='quote', description='Get a random quote')
async def quote(interaction):
    embed = discord.Embed(title="Quote", color=discord.Color.blurple())
    quotes_data = load_quotes()
    if quotes_data:
        quote_sets = quotes_data.get('quote_sets', [])
        if quote_sets:
            all_quotes = [quote['quotes'] for quote in quote_sets]
            flat_quotes = [quote for sublist in all_quotes for quote in sublist]
            if flat_quotes:
                random_quote = random.choice(flat_quotes)
                embed.add_field(name='', value=f"```{random_quote}```", inline=True)
            else:
                embed.add_field(name='Error', value="No quotes found in the database.", inline=True)
        else:
            embed.add_field(name='Error', value="No quote sets found in quotes.json.", inline=True)
    else:
        embed.add_field(name='Error', value="Failed to load quotes.json.", inline=True)
    
    await interaction.response.send_message(embed=embed)
