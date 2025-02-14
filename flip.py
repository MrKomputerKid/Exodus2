import random
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Coin Flip Command

@tree.command(name='flip', description='Flip a coin')
async def flip(interaction):
    responses = ['Heads',
                 'Tails']
    embed = discord.Embed(title="Coin Flip", color=discord.Color.blurple())
    response = random.choice(responses)
    embed.add_field(name='\U0001FA99', value=response, inline=False)
    await interaction.response.send_message(embed=embed)