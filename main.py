# Copyright <2023> <Craig J. Wessel>

# Import the required modules.
import discord
import aiomysql
import asyncio
import logging
import os
import sys
import json
import signal
from weather import weather, setlocation, setunit, air
from eightball import eightball
from flip import flip
from remind import remind
from quotes import quote
from datetime import datetime
from errors import handle_error, on_error, on_command_error
from discord import app_commands
from discord.ext import tasks
from jokes import joke, add_joke_command
from remind import get_reminders, remove_reminder

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

env_vars = dict(os.environ)
discord_logger.debug(json.dumps(env_vars, indent=4))
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
client.tree = tree

# DB Definitions for the count.py game
count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'message', 'channel_id','greedy_message']

# Register each additional command
tree.add_command(weather)
tree.add_command(setlocation)
tree.add_command(setunit)
tree.add_command(flip)
tree.add_command(remind)
tree.add_command(quote)
tree.add_command(eightball)
tree.add_command(joke)
tree.add_command(add_joke_command)
tree.add_command(air)
tree.add_command(get_reminders)
tree.add_command(remove_reminder)

# Connect to the MariaDB database.
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

# Create the users table if it doesn't already exist
async def create_users_table(pool):
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    location VARCHAR(255),
                    unit CHAR(1)
                )
            ''')

# Create the reminders table if it doesn't already exist
async def create_reminders_table(pool):
    async with pool.acquire() as connection:
        async with connection.cursor() as cur:
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT,
                    reminder TEXT,
                    remind_time DATETIME
                )
            ''')

# Keep the MariaDB Connection Alive
@tasks.loop(minutes=5)
async def keep_alive(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")

# Check reminders
@tasks.loop(seconds=1)
async def check_reminders(pool):
    while True:
        now = datetime.now()

        # Connect to the database
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Fetch reminders that are due
                await cur.execute("SELECT user_id, reminder, remind_time FROM reminders WHERE remind_time <= %s", (now,))
                reminders = await cur.fetchall()

                # Process each due reminder
                for row in reminders:
                    user_id, reminder_message, remind_time = row

                    # Get the user object
                    user = client.get_user(user_id)

                    # Create a Discord embed for the reminder
                    embed = discord.Embed(title="DO IT", color=discord.Color.green())
                    embed.add_field(name="Message", value=reminder_message, inline=False)
                    embed.add_field(name="Remind Time", value=str(remind_time), inline=False)

                    # Send the embed as a direct message to the user
                    await user.send(embed=embed) # type: ignore

                    # Delete the reminder from the database
                    await cur.execute("DELETE FROM reminders WHERE user_id = %s AND reminder = %s AND remind_time = %s",
                                      (user_id, reminder_message, remind_time))
                    await conn.commit()

                    # Optional: Log the completion of the reminder task
                    print(f'Reminder sent to user {user_id} for message: {reminder_message}')

                # Sleep for a short duration before checking again
                await asyncio.sleep(1)

# Events
@client.event
async def on_ready():
    pool, connection = await connect_to_db()
    await create_users_table(pool)
    await create_reminders_table(pool)
    await tree.sync()
    keep_alive.start(pool)  # Start the keep-alive task
    check_reminders.start(pool)  # Start the check reminders task
    print(f'We have logged in as {client.user}')

# Shutdown cleanup commands
async def cleanup_before_shutdown():
    await save_bot_state()
    await log_shutdown_event()
    await close_database_connection()

async def save_bot_state():
    # Example: Save user preferences to a JSON file
    user_preferences = {'user1': {'theme': 'dark', 'language': 'en'}, 'user2': {
        'theme': 'light', 'language': 'fr'}}
    with open('user_preferences.json', 'w') as file:
        json.dump(user_preferences, file)

async def log_shutdown_event():
    # Example: Log shutdown event to a file
    logging.basicConfig(filename='bot_shutdown.log', level=logging.INFO)
    logging.info('Bot is shutting down.')

async def close_database_connection():
    pool = None  # Initialize pool outside the try block

    try:
        # Retrieve connection details from environment variables
        host = os.getenv('DB_HOST')
        port = 3306
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        db = os.getenv('DB_DATABASE')

        # Establish the connection
        pool = await aiomysql.create_pool(host=host, port=port, user=user, password=password, db=db)

        # Add code here to perform any necessary database operations before closing

    finally:
        if pool:
            pool.close()
            await pool.wait_closed()

# Commands begin here.
# About this bot.
@tree.command(name='about', description='About this bot')
async def about(interaction):
    embed = discord.Embed(title="About", color=discord.Color.blurple())
    description = 'Exodus2 is the successor to the old Exodus IRC bot re-written for Discord. I know many bots like this exist, but I wanted to write my own.'
    embed.add_field(name="", value=description, inline=False)
    await interaction.response.send_message(embed=embed)

# Ping.
@tree.command(name='ping', description='Ping command')
async def ping(interaction):
    embed = discord.Embed(title="Ping", color=discord.Color.blurple())
    response = 'PONG!'
    embed.add_field(name='Response', value=response, inline=False)
    await interaction.response.send_message(embed=embed)

# Help
@tree.command(name="help", description="Show help information")
async def help(interaction):
    embed = discord.Embed(title="Help", color=discord.Color.blurple())
    for cmd in tree.walk_commands():
        embed.add_field(name=cmd.name, value=cmd.description, inline=False)
    await interaction.response.send_message(embed=embed)

# Sync Command! ONLY THE OWNER CAN DO THIS!
@tree.command(name='sync', description='Owner only!')
async def sync(interaction: discord.Interaction):
    owner_id = os.getenv('OWNER_ID')
    if str(interaction.user.id) == owner_id:  # Check if the user is the owner.
        try:
            await tree.sync()
            await interaction.response.send_message('Tree has been synced!')
            print('Command tree synced.')
        except Exception as e:
            print(e)
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

# Shutdown command. ONLY THE OWNER CAN DO THIS!
@tree.command(name='shutdown', description='Gracefully kill the bot. OWNER ONLY!')
async def shutdown(interaction):
    # Get the owner ID from environment variable
    owner_id = os.getenv('OWNER_ID')

    if str(interaction.user.id) == owner_id:  # Check if the user is the owner
        await interaction.response.send_message("Shutting down...")
        await cleanup_before_shutdown()
        await client.close()
    else:
        await interaction.response.send_message("You do not have permission to shut down the bot.")

# Restart the bot. ONLY THE OWNER CAN DO THIS!
@tree.command(name='restart', description='Gracefully reboot the bot. OWNER ONLY!')
async def restart(interaction):
    # Get the owner ID from environment variable
    owner_id = os.getenv('OWNER_ID')

    if str(interaction.user.id) == owner_id:  # Check if the user is the owner.
        await interaction.response.send_message('Rebooting...')
        await cleanup_before_shutdown()
        await client.close()

        # Restart the bot
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        await interaction.response.send_message('You do not have permission to reboot the bot.')

async def main():
    await client.start(os.getenv('DISCORD_BOT_TOKEN'))

def shutdown(signal, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(client.close())
    loop.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown, sig, None)
    try:
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        loop.close()
