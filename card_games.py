import random
import os
import logging
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

    async def initialize(self):
        # Perform any asynchronous setup here if needed
        pass

    async def create_deck(self):
        for suit in self.suits:
            for rank in self.ranks:
                self.deck.append((suit, rank))

    async def shuffle_deck(self):
        random.shuffle(self.deck)

    async def deal_card(self):
        return self.deck.pop()

    async def calculate_score(self, hand):
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
    
    async def initialize(self):
        # Perform any async setup here if needed.
        pass

    async def create_deck(self):
        for suit in self.suits:
            for rank in self.ranks:
                self.deck.append((suit, rank))

    async def shuffle_deck(self):
        random.shuffle(self.deck)

    async def deal_card(self):
        return self.deck.pop()

    async def calculate_score(self, hand):
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
    
# Blackjack command.

@tree.command(name="blackjack", description="Play blackjack!")
async def blackjack(interaction):
    play_again = True
    while play_again:
        game = await Blackjack()  # Use 'await' when instantiating an async class
        player_hand = [await game.deal_card(), await game.deal_card()]
        dealer_hand = [await game.deal_card(), await game.deal_card()]
        await interaction.response.send_message(f'Your hand: {player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}')
        await interaction.followup.send(f'Dealer hand: {dealer_hand[0][1]} of {dealer_hand[0][0]}, X')

        player_score = await game.calculate_score(player_hand)
        dealer_score = await game.calculate_score(dealer_hand)

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
        game = await Poker()  # Use 'await' when instantiating an async class
        player_hand = [await game.deal_card(), await game.deal_card(), await game.deal_card(), await game.deal_card(), await game.deal_card()]
        dealer_hand = [await game.deal_card(), await game.deal_card(), await game.deal_card(), await game.deal_card(), await game.deal_card()]
        await interaction.response.send_message(f'Your hand: {player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}, {player_hand[2][1]} of {player_hand[2][0]}, {player_hand[3][1]} of {player_hand[3][0]}, {player_hand[4][1]} of {player_hand[4][0]}')
        await interaction.followup.send('Type the numbers of the cards you want to discard (e.g., `1 3` to discard the first and third cards).')

        msg = await client.wait_for('message')
        discards = [int(i)-1 for i in msg.content.split()]
        for i in sorted(discards, reverse=True):
            player_hand.pop(i)
            player_hand.append(await game.deal_card())

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