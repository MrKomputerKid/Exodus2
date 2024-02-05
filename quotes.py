import discord
import random 
import logging
import os
import sys
from discord import app_commands
from discord.ext import commands, tasks

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Quotes for the Quote Command

quotes=[
    "<Leo7Mario> I want to make an IRC Bot, is there a way to make one in HTML?",
    "<`> Gerbils",
    "<|> Morse code is the best encryption algorhythm ever.",
    "<erno> Hmmm. I've lost a machine. Literally LOST. It responds to ping, it works completely, I just can't figure out where in my apartment it is.",
    "<Ubre> I'M RETARDED!",
    "<KK> Immo go rape my eyes.",
    "<KomputerKid> Hey did you know if you type your password in it shows up as stars! *********** See? "
    "<JacobGuy7800> mariospro "
    "<JacobGuy7800> Wait, DAMMIT",
    "<billy_mccletus> The onlee wuhn whose gunna be marryin' mah sister is gunna be me.",
    "<maxell> He just needs to realize we're one giant schizophrenic cat floating in a void...",
    "<KomputerKid> Why are you gae?",
    "<|> The holy bobble says 'Fuck you'",
    "<psychobat> https://www.youtube.com/watch?v=HqF_nPbX_Ow "
    "<Amity> Amity has quit. (Shutting down...) "
    "<lily> Amity did not expect the spanish inquisition.",
    "<psychobat> ?quote "
    "<psychobat> https://www.youtube.com/watch?v=HqF_nPbX_Ow "
    "<Amity> Amity has quit. (Shutting down...) "
    "<lily> Amity did not expect the spanish inquisition. "
    "<Leo7Mario> Leo7Mario has quit. (Shutting down...) "
    "<psychobat> Nor did Leo7Mario.",
]

# Quote command. Pulls from quotes above.

@tree.command(name='quote', description='Get a random quote from the old IRC Days')
async def quote(interaction):
    random_quote = random.choice(quotes)
    await interaction.response.send_message(random_quote)