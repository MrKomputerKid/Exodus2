import discord
from discord import app_commands
from discord.ext import tasks
from datetime import datetime, timedelta
import aiomysql
import logging
import re
import asyncio
import os
import sys
import json

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

async def connect_to_db():
    pool = await aiomysql.create_pool(
        host=os.getenv('DB_HOST'),
        port=3306,
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_DATABASE'),
        autocommit=True
    )
    connection = await pool.acquire()
    return pool, connection

# Remind me command!

@tree.command(name='remind', description='Set a Reminder!')
async def remind(interaction, reminder_time: str, *, reminder: str):
    remind_time = parse_reminder_time(reminder_time)

    pool, conn = await connect_to_db() # Unpack the tuple here if necessary.
    async with conn.cursor() as cur:
        sql = "INSERT INTO reminders (user_id, reminder, remind_time) VALUES (%s, %s, %s)"
        val = (interaction.user.id, reminder, remind_time)
        await cur.execute(sql, val)

    embed = discord.Embed(title="Reminder Set", color=discord.Color.green())
    embed.add_field(name="Reminder", value=reminder, inline=False)
    embed.add_field(name="Remind Time", value=str(remind_time), inline=False)

    await interaction.response.send_message(embed=embed)

def parse_reminder_time(reminder_time: str) -> datetime:
    hours, minutes, seconds = 0, 0, 0

    if 'h' in reminder_time:
        hours_str, reminder_time = reminder_time.split('h', 1)
        hours = int(hours_str)

    if 'm' in reminder_time:
        minutes_str, reminder_time = reminder_time.split('m', 1)
        minutes = int(minutes_str)

    if 's' in reminder_time:
        seconds_str, reminder_time = reminder_time.split('s', 1)
        seconds = int(seconds_str)

    delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    return datetime.now() + delta
