# Copyright <2023> <Craig J. Wessel>
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Import the required modules.s

import discord
import random
import requests
import mysql.connector
import logging
import re
import asyncio
import os
import signal
import datetime
from discord import app_commands
from discord.ext import tasks


logging.basicConfig(level=logging.DEBUG)

intents = discord.Intents.default()

intents.members = True

client = discord.Client(intents=intents)

tree = app_commands.CommandTree(client)

# Connect to the MariaDB database.
db = mysql.connector.connect(
    host='UR_HOST',
    user='UR_USER',
    password='UR_PW',
    database='UR_DB'
)

cursor = db.cursor()

# Keep the MariaDB Connection Alive 
@tasks.loop(minutes=5)
async def keep_alive():
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    if result is None:
        db.ping(reconnect=True)

# Create the users table if it doesn't already exist

cursor.execute('''
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
    "<Sony> Hello. We are from Sony Pictures",
    "Kim Jong Un has joined! "
    "<picky1004> WTF!!!! KIM JONG UN???? "
    "<Kim Jong Un> HAHAHAHAHA YES! "
    "<picky1004> Guys! Kim jong un is here!",
    "<KomputerKid> Why are you gae?",
    "<DDX> ITS A FEATURE NOT A BUG /hurrdurr",
    "<jakejh> But what if you are already gae?",
    "<JelleTheWhale> Whelp! It's official. Tower Brdige is no more. "
    "<KomputerKid> Hu - DID SHE DIE? "
    "<KomputerKid> IS LONDON BRIDGE DOWN?"
]

# Definitions for the weather database.

def get_user_location(user_id):
    cursor.execute('SELECT location FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def set_user_location(user_id, location):
    cursor.execute('UPDATE users SET location = %s WHERE id = %s', (location, user_id))
    if cursor.rowcount == 0:
        cursor.execute('INSERT INTO users (id, location) VALUES (%s, %s)', (user_id, location))
    db.commit()

def get_user_unit(user_id):
    cursor.execute('SELECT unit FROM users WHERE id = %s', (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    return None

def set_user_unit(user_id, unit):
    cursor.execute('UPDATE users SET unit = %s WHERE id = %s', (unit, user_id))
    if cursor.rowcount == 0:
        cursor.execute('INSERT INTO users (id, unit) VALUES (%s, %s)', (user_id, unit))
    db.commit()

# Classes and scripting for the Blackjack, poker, and play commands.

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

# Weather command. Pulls data from Openweathermap API and stores data in a MariaDB database.

@tree.command(name="weather", description="Fetch the weather!")
async def weather(interaction, location: str = None, unit: str = None):
    # Replace UR_API_KEY with your own OpenWeatherMap API key
    api_key = 'UR_API_KEY'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric'
    response = requests.get(url)
    data = response.json()
    if location is None:
        location = get_user_location(interaction.user.id)
        if not location:
            await interaction.response.send_message('Please specify a location or set your location using the `setlocation` command.')
            return
        if unit is None:
            unit = get_user_unit(interaction.user.id)
            if not unit:
                unit = 'C'
    if data['cod'] == 200:
        temp_celsius = data['main']['temp']
        description = data['weather'][0]['description']
        if unit == 'F':
            temp_fahrenheit = temp_celsius * 9/5 + 32
            await interaction.response.send_message(f'The current temperature in {location} is {temp_fahrenheit:.1f}°F with {description}.')
        elif unit == 'K':
            temp_kelvin = temp_celsius + 273.15
            await interaction.response.send_message(f'The current temperature in {location} is {temp_kelvin:.2f}°K with {description}.')
        else:
            await interaction.response.send_message(f'The current temperature in {location} is {temp_celsius}°C with {description}.')
    else:
        await interaction.response.send_message(f'Sorry, I couldn\'t find weather information for {location}.')

# Remind Me Command

@tree.command(name='remind', description='Set a Reminder!')
async def remind(ctx, reminder_time: str, *, reminder: str):
    remind_time = datetime.strptime(reminder_time, '%Y-%m-%d %H:%M:%S')
    mycursor = db.cursor()
    sql = "INSERT INTO reminders (user_id, reminder, remind_time) VALUES (%s, %s, %s)"
    val = (ctx.author.id, reminder, remind_time)
    mycursor.execute(sql, val)
    db.commit()
    await ctx.send(f'Reminder set! I will remind you at {reminder_time}.')

async def check_reminders():
    while True:
        now = datetime.now()
        mycursor = db.cursor()
        mycursor.execute("SELECT * FROM reminders WHERE remind_time <= %s", (now,))
        reminders = mycursor.fetchall()
        for row in reminders:
            user_id, reminder_message, _ = row
            user = client.get_user(user_id)
            await user.send(f'DO IT: {reminder_message}')
            mycursor.execute("DELETE FROM reminders WHERE user_id = %s AND reminder = %s", (user_id, reminder_message))
            db.commit()
        await asyncio.sleep(1)
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
async def setlocation(interaction, *, location: str):
    set_user_location(interaction.user.id, location)
    await interaction.response.send_message(f'Your location has been set to {location}.')

# Set preferred units for the weather command. Stores this information in a mariadb database.

@tree.command(name='setunit', description='Set your preferred units')
async def setunit(interaction, *, unit: str):
    if unit.upper() not in ['C', 'F', 'K']:
        await interaction.response.send_message('Invalid unit. Please specify either `C` for Celsius, `F` for Fahrenheit or `K` for Kelvin.')
        return
    set_user_unit(interaction.user.id, unit.upper())
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

# Events begin here

@client.event
async def on_ready():
    # Replace YOUR_GUILD_ID with your actual Guild ID
    await tree.sync(guild=discord.Object(id=YOUR_GUILD_ID))
    print("Ready!")
    await check_reminders()
    # Replace UR_BOT_TKN with your bot's token!
client.run('UR_BOT_TKN')
