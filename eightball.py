import random
import logging
import discord
from discord import app_commands
from discord.ext import tasks, commands

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 8ball command. It will tell you if you don't specify a question that you need to specify one.

@tree.command(name='8ball', description='Magic 8ball!')
async def eightball(interaction, *, question: str = None):
    responses = ['It is certain.',
                 'It is decidedly so.',
                 'Without a doubt.',
                 'Yes - definitely.',
                 'You may rely on it.',
                 'As I see it, yes.',
                 'Most likely.',
                 'Outlook good.',
                 'Yes.',
                 'Signs point to yes.',
                 'Reply hazy, try again.',
                 'Ask again later.',
                 'Better not tell you now.',
                 'Cannot predict now.',
                 'Concentrate and ask again.',
                 'Don\'t count on it.',
                 'My reply is no.',
                 'My sources say no.',
                 'Outlook not so good.',
                 'Very doubtful.']
    if question is None:
        embed = discord.Embed(title="ERROR", color=discord.Color.red())
        response = 'Please specify a question to use the 8ball.'
        embed.add_field(name='', value=response, inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        response = random.choice(responses)
        embed = discord.Embed(title="Response", color=discord.Color.black())
        embed.add_field(name='Question \U0001F3B1', value=question, inline=False)
        embed.add_field(name='\U0001F3B1', value=response, inline=False)
        await interaction.response.send_message(embed=embed)
