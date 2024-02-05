import logging
import random
import os
import asyncio
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

class Roulette:
    def __init__(self):
        self.gun = []
        self.bullets = [1]
        self.chambers = 6

        self.create_game()
        self.spin_chamber()

    def create_game(self):
        for bullet in self.bullets:
            for chamber in range(1, self.chambers + 1):
                self.gun.append((bullet, chamber))

    def spin_chamber(self):
        random.shuffle(self.gun)

# Russian Roulette Command

@tree.command(name='roulette', description='Play Russian Roulette!')
async def roulette(interaction):   
        game = Roulette()
        await interaction.response.send_message("Are you ready to pull the trigger? Type `s` to continue or `q` to pussy out.")
        msg = await client.wait_for(msg)
        if msg.content.lower() != 'q':
            bullet, chamber = game.gun.pop(0)
            if bullet == 1 and chamber == 1:
                await interaction.followup.send("BLAMMO! You are dead!")
            else:
                await interaction.followup.send("Click! You survived!")
        else:
            await interaction.followup.send("WIMP! You pussied out!")
