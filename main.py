# Copyright <2023> <Craig J. Wessel>

# Import the required modules.
import discord
import random
import requests
import aiomysql
import logging
import re
import asyncio
import os
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import tasks, commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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
    return pool


# Keep the MariaDB Connection Alive
@tasks.loop(minutes=5)
async def keep_alive(pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")

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
    "<KomputerKid> Why are you gae?"
]

# Definitions for the weather database.

async def set_user_location(user_id, location, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('UPDATE users SET location = %s WHERE id = %s', (location, user_id))
            if cur.rowcount == 0:
                await cur.execute('INSERT INTO users (id, location) VALUES (%s, %s)', (user_id, location))
        await conn.commit()

async def set_user_unit(user_id, unit, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute('UPDATE users SET unit = %s WHERE id = %s', (unit, user_id))
            if cur.rowcount == 0:
                await cur.execute('INSERT INTO users (id, unit) VALUES (%s, %s)', (user_id, unit))
        await conn.commit()

async def get_user_location(user_id, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT location FROM users WHERE id = %s", (user_id,))
            result = await cur.fetchone()
            return result[0] if result else None

async def get_user_unit(user_id, pool):
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT unit FROM users WHERE id = %s", (user_id,))
            result = await cur.fetchone()
            return result[0] if result else None


# Classes and scripting for the Blackjack, poker, and play commands.

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

class Blackjack:
    def __init__(self):
        self.deck = []
        self.suits = ('Hearts', 'Diamonds', 'Clubs', 'Spades')
        self.values = {'Two':2, 'Three':3, 'Four':4, 'Five':5, 'Six':6, 'Seven':7, 'Eight':8,
                       'Nine':9, 'Ten':10, 'Jack':10, 'Queen':10, 'King':10, 'Ace':11}
        self.ranks = ('Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
                      'Jack', 'Queen', 'King', 'Ace')
        self.create_deck()
        self.shuffle_deck()

    def create_deck(self):
        for suit in self.suits:
            for rank in self.ranks:
                self.deck.append((suit, rank))

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop()

    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            rank = card[1]
            score += self.values[rank]
            if rank == 'Ace':
                aces += 1
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

class Poker:
    def __init__(self):
        self.deck = []
        self.suits = ('Hearts', 'Diamonds', 'Clubs', 'Spades')
        self.values = {'Two':2, 'Three':3, 'Four':4, 'Five':5, 'Six':6, 'Seven':7, 'Eight':8,
                       'Nine':9, 'Ten':10, 'Jack':11, 'Queen':12, 'King':13, 'Ace':14}
        self.ranks = ('Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
                      'Jack', 'Queen', 'King', 'Ace')
        self.create_deck()
        self.shuffle_deck()

    def create_deck(self):
        for suit in self.suits:
            for rank in self.ranks:
                self.deck.append((suit, rank))

    def shuffle_deck(self):
        random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop()

    def calculate_score(self, hand):
        score = 0
        ranks = [card[1] for card in hand]
        rank_counts = {rank: ranks.count(rank) for rank in ranks}
        if len(set(ranks)) == 5:
            if max([self.values[rank] for rank in ranks]) - min([self.values[rank] for rank in ranks]) == 4:
                score += 100
            if len(set([card[0] for card in hand])) == 1:
                score += 1000
        if 4 in rank_counts.values():
            score += 750
        elif 3 in rank_counts.values() and 2 in rank_counts.values():
            score += 500
        elif 3 in rank_counts.values():
            score += 250
        elif len([count for count in rank_counts.values() if count == 2]) == 2:
            score += 100
        elif 2 in rank_counts.values():
            score += 50
        return score

# Commands begin here.

# Blackjack command.

@tree.command(name="blackjack", description="Play blackjack!")
async def blackjack(interaction):
    play_again = True
    while play_again:
        game = Blackjack()
        player_hand = [game.deal_card(), game.deal_card()]
        dealer_hand = [game.deal_card(), game.deal_card()]
        await interaction.response.send_message(f'Your hand: {player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}')
        await interaction.followup.send(f'Dealer hand: {dealer_hand[0][1]} of {dealer_hand[0][0]}, X')

        player_score = game.calculate_score(player_hand)
        dealer_score = game.calculate_score(dealer_hand)

        if player_score == 21:
            await interaction.followup.send('Blackjack! You win!')

        while player_score < 21:
            await interaction.followup.send('Type `h` to hit or `s` to stand.')
            msg = await client.wait_for('message')
            if msg.content.lower() == 'h':
                player_hand.append(game.deal_card())
                player_score = game.calculate_score(player_hand)
                hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in player_hand])
                await interaction.followup.send(f'Your hand: {hand_text}')
            else:
                break

        if player_score > 21:
            await interaction.followup.send('Bust! You lose.')

        while dealer_score < 17:
            dealer_hand.append(game.deal_card())
            dealer_score = game.calculate_score(dealer_hand)

        hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in dealer_hand])
        await interaction.followup.send(f'Dealer hand: {hand_text}')

        if dealer_score > 21:
            await interaction.followup.send('Dealer busts! You win!')
        elif dealer_score > player_score:
            await interaction.followup.send('Dealer wins!')
        elif dealer_score < player_score:
            await interaction.followup.send('You win!')
        else:
            await interaction.followup.send('Tie!')

        await interaction.followup.send('Do you want to play again? Type `y` for yes or `n` for no.')
        msg = await client.wait_for('message')
        if msg.content.lower() != 'y':
            play_again = False

# Poker command

@tree.command(name="poker", description="Play poker!")
async def poker(interaction):
    play_again = True
    while play_again:
        game = Poker()
        player_hand = [game.deal_card(), game.deal_card(), game.deal_card(), game.deal_card(), game.deal_card()]
        dealer_hand = [game.deal_card(), game.deal_card(), game.deal_card(), game.deal_card(), game.deal_card()]
        await interaction.response.send_message(f'Your hand: {player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}, {player_hand[2][1]} of {player_hand[2][0]}, {player_hand[3][1]} of {player_hand[3][0]}, {player_hand[4][1]} of {player_hand[4][0]}')
        await interaction.followup.send('Type the numbers of the cards you want to discard (e.g., `1 3` to discard the first and third cards).')

        msg = await client.wait_for('message')
        discards = [int(i)-1 for i in msg.content.split()]
        for i in sorted(discards, reverse=True):
            player_hand.pop(i)
            player_hand.append(game.deal_card())

        hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in player_hand])
        await interaction.followup.send(f'Your new hand: {hand_text}')

        player_score = game.calculate_score(player_hand)
        dealer_score = game.calculate_score(dealer_hand)

        hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in dealer_hand])
        await interaction.followup.send(f'Dealer hand: {hand_text}')

        if dealer_score > player_score:
            await interaction.followup.send('Dealer wins!')
        elif dealer_score < player_score:
            await interaction.followup.send('You win!')
        else:
            await interaction.followup.send('Tie!')

        await interaction.followup.send('Do you want to play again? Type `y` for yes or `n` for no.')
        msg = await client.wait_for('message')
        if msg.content.lower() != 'y':
            play_again = False

# Russian Roulette Command

@tree.command(name='roulette', description='Play Russian Roulette!')
async def roulette(interaction):   
        game = Roulette()
        await interaction.response.send_message("Are you ready to pull the trigger? Type `s` to continue or `q` to pussy out.")
        msg = await client.wait_for('message')
        if msg.content.lower() != 'q':
            bullet, chamber = game.gun.pop(0)
            if bullet == 1 and chamber == 1:
                await interaction.followup.send("BLAMMO! You are dead!")
            else:
                await interaction.followup.send("Click! You survived!")
        else:
            await interaction.followup.send("WIMP! You pussied out!")

# Weather command! Fetch the weather!

@tree.command(name="weather", description="Fetch the weather!")
async def weather(interaction, location: str = None, state_province: str = None, unit: str = None):
    api_key = os.getenv('OPENWEATHERMAP_API_KEY')
    data = {}  # Initialize data variable

    if location is None:
        pool, connection = await connect_to_db()
        location = await get_user_location(interaction.user.id, pool)

        if location:
            unit = await get_user_unit(interaction.user.id, pool)
            if not unit:
                unit = 'C'
        else:
            await interaction.response.send_message('Please specify a location or set your location using the `setlocation` command.')
            await pool.release(connection)
            return

        await pool.release(connection)  # Release the connection back to the pool

    # Make the API request with the correct location
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    print(f"DEBUG: API Response: {data}")

    full_location = f"{location}, {state_province}" if state_province else location

    if data and data.get('cod') == 200:
        temp_celsius = data['main']['temp']
        description = data['weather'][0]['description']
        if unit == 'F':
            temp_fahrenheit = temp_celsius * 9/5 + 32
            await interaction.response.send_message(f'The current temperature in {full_location} is {temp_fahrenheit:.1f}°F with {description}.')
        elif unit == 'K':
            temp_kelvin = temp_celsius + 273.15
            await interaction.response.send_message(f'The current temperature in {full_location} is {temp_kelvin:.2f}°K with {description}.')
        else:
            await interaction.response.send_message(f'The current temperature in {full_location} is {temp_celsius}°C with {description}.')
    else:
        await interaction.response.send_message(f'Sorry, I couldn\'t find weather information for {full_location}.')


# Remind Me Command

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
@tasks.loop(seconds=1)
async def check_reminders(pool):
    while True:
        now = datetime.now()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id, reminder, remind_time FROM reminders WHERE remind_time <= %s", (now,))
                reminders = await cur.fetchall()
                for row in reminders:
                    user_id, reminder_message, remind_time = row
                    user = client.get_user(user_id)
                    await user.send(f'DO IT: {reminder_message}')
                    await cur.execute("DELETE FROM reminders WHERE user_id = %s AND reminder = %s AND remind_time = %s", (user_id, reminder_message, remind_time))
                    await conn.commit()

# 8ball command. It will tell you if you don't specify a question that you need to specify one.

@tree.command(name='8ball', description='Magic 8ball!')
async def _8ball(interaction, *, question: str = None):
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
        await interaction.response.send_message('Please specify a question to use the 8ball.')
    else:
        response = random.choice(responses)
        await interaction.response.send_message(response)

# Quote command. Pulls from quotes above.

@tree.command(name='quote', description='Get a random quote from the old IRC Days')
async def quote(interaction):
    random_quote = random.choice(quotes)
    await interaction.response.send_message(random_quote)

# Set location for the weather command. Stores this information in a mariadb database.

@tree.command(name='setlocation', description='Set your preferred location')
async def setlocation(interaction, *, location: str, state_province: str):
    pool, connection = await connect_to_db()
    full_location = f"{location}, {state_province}" if state_province else location
    await set_user_location(interaction.user.id, full_location, pool)
    await pool.release(connection)
    await interaction.response.send_message(f'Your location has been set to {location}.')

# Set preferred units for the weather command. Stores this information in a mariadb database.

@tree.command(name='setunit', description='Set your preferred units')
async def setunit(interaction, *, unit: str):
    if unit.upper() not in ['C', 'F', 'K']:
        await interaction.response.send_message('Invalid unit. Please specify either `C` for Celsius, `F` for Fahrenheit or `K` for Kelvin.')
        return
    pool, connection = await connect_to_db()
    await set_user_unit(interaction.user.id, unit.upper(), pool)
    await pool.release(connection)
    await interaction.response.send_message(f'Your preferred temperature unit has been set to {unit.upper()}.')

# Coin Flip Command

@tree.command(name='flip', description='Flip a coin')
async def flip(interaction):
    responses = ['Heads',
                 'Tails']
    response = random.choice(responses)
    await interaction.response.send_message(response)

# About this bot.

@tree.command(name='about', description='About this bot')
async def about(interaction):
    response = 'Exodus2 is the successor to the old Exodus IRC bot re-written for Discord. I know many bots like this exist, but I wanted to write my own.'
    await interaction.response.send_message(response)

# Ping.

@tree.command(name='ping', description='Ping command')
async def ping(interaction):
    response = 'PONG!'
    await interaction.response.send_message(response)

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
    if interaction.user.id == os.getenv('OWNER_ID'):
        await tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

# Events begin here

@client.event
async def on_ready():
    pool = await connect_to_db()
    await create_users_table(pool)
    keep_alive.start(pool)  # Start the keep-alive task
    check_reminders.start(pool)
    print('Ready!')

async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!sync'):
        if message.author.id == int(os.getenv('OWNER_ID')):
            await sync_tree()
        await message.channel.send('Command tree synced.')
    else:
        await message.channel.send('You must be the owner to use this command!')

async def sync_tree():
    await tree.sync()
    print('Command tree synced.')

client.run(os.getenv('DISCORD_TOKEN'))