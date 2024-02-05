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
        self.values = {'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5, 'Six': 6, 'Seven': 7, 'Eight': 8,
                       'Nine': 9, 'Ten': 10, 'Jack': 10, 'Queen': 10, 'King': 10, 'Ace': 11}
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
        if not self.deck:
            # If the deck is empty, create and shuffle a new one
            await self.create_deck()
            await self.shuffle_deck()

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

@tree.command(name="blackjack", description="Play blackjack!")
async def blackjack(interaction):
    play_again = True

    while play_again:
        game = Blackjack()
        player_hand = [game.deal_card(), game.deal_card()]
        dealer_hand = [game.deal_card(), game.deal_card()]

        # Send the initial embed
        embed = discord.Embed(title="Blackjack", description=f"Your hand: {player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}", color=0xd3d3d3)
        
        message = await interaction.response.send_message(embed=embed)

        # Add reactions to the original interaction message
        await interaction.message.add_reaction('\U00002705')  # Checkmark (✅) for Hit
        await interaction.message.add_reaction('\U0000274C')  # Cross (❌) for Stand


        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ['\U00002705', '\U0000274C']

        try:
            reaction, user = await tree.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timeout! Game Over.")
            return

        if str(reaction.emoji) == '\U00002705':
            player_hand.append(game.deal_card())
            hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in player_hand])
            embed.description = f"Your hand: {hand_text}"
            await interaction.followup.send(embed=embed)
        else:
            break

        player_score = game.calculate_score(player_hand)

        if player_score > 21:
            embed.description = 'Bust! You lose.'
            await interaction.followup.send(embed=embed)
            play_again = False

    while game.calculate_score(dealer_hand) < 17:
        dealer_hand.append(game.deal_card())

    hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in dealer_hand])
    embed.description = f'Dealer hand: {hand_text}'
    await interaction.followup.send(embed=embed)

    if game.calculate_score(dealer_hand) > 21:
        embed.description = 'Dealer busts! You win!'
    elif game.calculate_score(dealer_hand) > player_score:
        embed.description = 'Dealer wins!'
    elif game.calculate_score(dealer_hand) < player_score:
        embed.description = 'You win!'
    else:
        embed.description = "It's a tie!"

    await interaction.followup.send(embed=embed)
    await interaction.followup.send('Do you want to play again? React with \U00002705 for yes or \U0000274C for no.')

    try:
        reaction, user = await tree.wait_for('reaction_add', timeout=60.0, check=lambda r, u: u == interaction.user and str(r.emoji) in ['\U00002705', '\U0000274C'])
    except asyncio.TimeoutError:
        await interaction.followup.send("Timeout! Game Over.")
        return

    if str(reaction.emoji) == '\U00002705':
        play_again = True
    else:
        play_again = False


@tree.command(name="poker", description="Play poker!")
async def poker(interaction):
    play_again = True

    while play_again:
        game = Poker()
        player_hand = [await game.deal_card() for _ in range(5)]
        dealer_hand = [await game.deal_card() for _ in range(5)]

        embed = discord.Embed(title="Poker", description=f"Your hand: {', '.join([f'{card[1]} of {card[0]}' for card in player_hand])}", color=0xd3d3d3)

        message = await interaction.response.send_message(embed=embed)

        await interaction.message.add_reaction('\U00002705')  # Checkmark (✅) for Discard
        await interaction.message.add_reaction('\U0000274C')  # Cross (❌) for Keep

        def check(reaction, user):
            return user == interaction.user and str(reaction.emoji) in ['\U00002705', '\U0000274C']

        try:
            reaction, user = await tree.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await interaction.followup.send("Timeout! Game Over.")
            return

        if str(reaction.emoji) == '\U00002705':
            discards = [0, 1, 2, 3, 4]  # Example: discard all cards
            for i in sorted(discards, reverse=True):
                player_hand.pop(i)
                player_hand.append(await game.deal_card())

            hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in player_hand])
            embed.description = f'Your new hand: {hand_text}'
            await interaction.followup.send(embed=embed)
        else:
            break

        player_score = game.calculate_score(player_hand)
        dealer_score = game.calculate_score(dealer_hand)

        hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in dealer_hand])
        embed.description = f'Dealer hand: {hand_text}'
        await interaction.followup.send(embed=embed)

        if dealer_score > player_score:
            embed.description = 'Dealer wins!'
        elif dealer_score < player_score:
            embed.description = 'You win!'
        else:
            embed.description = "It's a tie!"

        await interaction.followup.send(embed=embed)
        message = await interaction.followup.send('Do you want to play again? React with \U00002705 for yes or \U0000274C for no.')
        await interaction.message.add_reaction('\U00002705')  # Checkmark (✅) for Yes
        await interaction.message.add_reaction('\U0000274C')  # Cross (❌) for No

        try:
            reaction, user = await tree.wait_for('reaction_add', timeout=60.0, check=lambda r, u: u == interaction.user and str(r.emoji) in ['\U00002705', '\U0000274C'])
        except asyncio.TimeoutError:
            await interaction.followup.send("Timeout! Game Over.")
            return

        if str(reaction.emoji) == '\U00002705':
            play_again = True
        else:
            play_again = False

