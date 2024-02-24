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

# Quote command. Pulls a quote from the json quote database, and allows the user to specify a number and set name if one is available.

@tree.command(name='quote', description='Get a random quote from the old IRC days, or specify one in one of our 3 databases')
async def quote(interaction, set_name: str = None, quote_number: str = None):
    embed = discord.Embed(title="Quote", color=discord.Color.blurple())
    quotes_data = load_quotes()
    
    if quotes_data:
        quote_sets = quotes_data.get('quote_sets', [])
        if quote_sets:
            if set_name:
                set_quotes = None
                for quote_set in quote_sets:
                    if quote_set['set_name'] == set_name:
                        set_quotes = quote_set['quotes']
                        break
                
                if set_quotes:
                    if quote_number:
                        try:
                            quote_number = int(quote_number)
                            if quote_number <= len(set_quotes):
                                quote = set_quotes[quote_number - 1]
                                truncated_quote = truncate_quote(quote)
                                embed.add_field(name='', value=f"```{truncated_quote}```", inline=True)
                            else:
                                embed = discord.Embed(title="Error", description=f"Quote number {quote_number} does not exist in set '{set_name}'.", color=discord.Color.red())
                        except ValueError:
                            embed = discord.Embed(title="Error", description=f"Invalid quote number: {quote_number}.", color=discord.Color.red())
                    else:
                        random_quote = random.choice(set_quotes)
                        truncated_quote = truncate_quote(random_quote)
                        embed.add_field(name='', value=f"```{truncated_quote}```", inline=True)
                else:
                    available_sets = ', '.join([quote_set['set_name'] for quote_set in quote_sets])
                    embed = discord.Embed(title="Error", description=f"Set '{set_name}' not found. Available sets: {available_sets}", color=discord.Color.red())
            else:
                all_quotes = [quote['quotes'] for quote in quote_sets]
                flat_quotes = [quote for sublist in all_quotes for quote in sublist]
                random_quote = random.choice(flat_quotes)
                truncated_quote = truncate_quote(random_quote)
                embed.add_field(name='', value=f"```{truncated_quote}```", inline=True)
        else:
            embed = discord.Embed(title="Error", description="No quote sets found in quotes.json.", color=discord.Color.red())
    else:
        embed = discord.Embed(title="Error", description="Failed to load quotes.json.", color=discord.Color.red())
    
    await interaction.response.send_message(embed=embed)