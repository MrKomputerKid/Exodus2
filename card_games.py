import random
import os
import logging
import asyncio
import discord
import reactionmenu
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
    while True:
        game = Blackjack()
        player_hand = [game.deal_card(), game.deal_card()]
        dealer_hand = [game.deal_card(), game.deal_card()]

        embed = discord.Embed(title="Blackjack", color=0xd3d3d3)
        embed.add_field(name="Your Hand", value=f"{player_hand[0][1]} of {player_hand[0][0]}, {player_hand[1][1]} of {player_hand[1][0]}", inline=False)
        message = await interaction.response.send_message(embed=embed)

        async def hit():
            player_hand.append(game.deal_card())
            hand_text = ', '.join([f'{card[1]} of {card[0]}' for card in player_hand])
            embed.set_field_at(0, name="Your Hand", value=hand_text, inline=False)
            await message.edit(embed=embed)

        async def stand():
            pass

        row = discord.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.success, label="Hit", custom_id="hit"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Stand", custom_id="stand")
        )

        await interaction.response.send_message("Choose your action:", components=[row])

        try:
            interaction = await client.wait_for("button_click", timeout=30)  # Wait for user's response
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Exiting game.")
            break

        if interaction.component.custom_id == "hit":
            await hit()
        elif interaction.component.custom_id == "stand":
            await stand()

        # Calculate player score
        player_score = game.calculate_score(player_hand)

        # Determine the winner
        if player_score > 21:
            result = "You busted! Dealer wins."
        else:
            while game.calculate_score(dealer_hand) < 17:
                dealer_hand.append(game.deal_card())
            dealer_score = game.calculate_score(dealer_hand)
            if dealer_score > 21 or player_score > dealer_score:
                result = "You win!"
            elif dealer_score > player_score:
                result = "Dealer wins."
            else:
                result = "It's a tie."

        # Update embed with game result
        embed.add_field(name="Result", value=result, inline=False)
        await message.edit(embed=embed)

        # Prompt for playing again
        await asyncio.sleep(3)  # Wait for a few seconds before prompting again
        await interaction.followup.send("Do you want to play again?", 
            [discord.ui.Button(style=discord.ButtonStyle.success, label="Yes"), discord.ui.Button(style=discord.ButtonStyle.danger, label="No")]
        )

        try:
            interaction = await client.wait_for("button_click", timeout=30)  # Wait for user's response
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Exiting game.")
            break

        if interaction.component.label == "No":
            await interaction.followup.send("Thanks for playing!")
            break

# Command begins here.

@tree.command(name="poker", description="Play poker!")
async def poker(interaction):
    while True:
        game = Poker()
        player_hand = [await game.deal_card() for _ in range(5)]
        dealer_hand = [await game.deal_card() for _ in range(5)]

        embed = discord.Embed(title="Poker", color=0xd3d3d3)
        embed.add_field(name="Your Hand", value=', '.join([f'{card[1]} of {card[0]}' for card in player_hand]), inline=False)
        message = await interaction.response.send_message(embed=embed)

        async def discard():
            pass

        async def keep():
            pass

        row = discord.ActionRow(
            discord.ui.Button(style=discord.ButtonStyle.success, label="Discard", custom_id="discard"),
            discord.ui.Button(style=discord.ButtonStyle.danger, label="Keep", custom_id="keep")
        )

        await interaction.response.send_message("Choose your action:", components=[row])

        try:
            interaction = await client.wait_for("button_click", timeout=30)  # Wait for user's response
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Exiting game.")
            break

        if interaction.component.custom_id == "discard":
            await discard()
        elif interaction.component.custom_id == "keep":
            await keep()

        # Calculate player score
        player_score = await game.calculate_score(player_hand)

        # Determine the winner
        # For simplicity, we can just display the player's score
        result = f"Your score: {player_score}"

        # Update embed with game result
        embed.add_field(name="Result", value=result, inline=False)
        await message.edit(embed=embed)

        # Prompt for playing again
        await asyncio.sleep(3)  # Wait for a few seconds before prompting again
        await interaction.followup.send("Do you want to play again?",
            [discord.ui.Button(style=discord.ButtonStyle.success, label="Yes"), discord.ui.Button(style=discord.ButtonStyle.danger, label="No")]
        )

        try:
            interaction = await client.wait_for("button_click", timeout=30)  # Wait for user's response
        except asyncio.TimeoutError:
            await interaction.followup.send("You took too long to respond. Exiting game.")
            break

        if interaction.component.label == "No":
            await interaction.followup.send("Thanks for playing!")
            break
