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
    # Use create_pool directly here
    async with aiomysql.create_pool(
        host=os.getenv('DB_HOST'),
        port=3306,
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_DATABASE'),
        autocommit=True
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                sql = "INSERT INTO reminders (user_id, reminder, remind_time) VALUES (%s, %s, %s)"
                val = (interaction.user.id, reminder, remind_time)
                await cur.execute(sql, val)
        await interaction.response.send_message(f'Reminder set! I will remind you at {remind_time}.')

def parse_reminder_time(reminder_time: str) -> datetime:
    # Implement your parsing logic here
    # Example: '2h30m' means 2 hours and 30 minutes
    # You need to convert this string into a timedelta object
    # You may use regular expressions to extract the time components

    # For simplicity, let's assume the input is in the format 'XhYmZs'
    hours, minutes, seconds = 0, 0, 0

    # Parse hours
    if 'h' in reminder_time:
        hours_str, reminder_time = reminder_time.split('h', 1)
        hours = int(hours_str)

    # Parse minutes
    if 'm' in reminder_time:
        minutes_str, reminder_time = reminder_time.split('m', 1)
        minutes = int(minutes_str)

    # Parse seconds
    if 's' in reminder_time:
        seconds_str, reminder_time = reminder_time.split('s', 1)
        seconds = int(seconds_str)

    # Calculate the total timedelta
    delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    return datetime.now() + delta