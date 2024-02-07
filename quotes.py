import discord
import random
import logging
from discord.ext import commands, app_commands
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Function to scrape quotes from the website
def scrape_quotes():
    quotes = []
    page_number = 1
    while True:
        url = f"https://bash-org-archive.com/?browse=&p{page_number}"
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            quote_elements = soup.find_all('div', class_='qt')
            if not quote_elements:
                break
            for quote_element in quote_elements:
                quote_text = quote_element.find('div', class_='quote').text.strip()
                quotes.append(quote_text)
            page_number += 1
        else:
            break
    return quotes

# Quotes for the Quote Command

tt_quotes=[
    "<Leo7Mario> I want to make an IRC Bot, is there a way to make one in HTML?",
    "<`> Gerbils",
    "<|> Morse code is the best encryption algorhythm ever.",
    "<erno> Hmmm. I've lost a machine. Literally LOST. It responds to ping, it works completely, I just can't figure out where in my apartment it is.",
    "<Ubre> I'M RETARDED!",
    "<KK> Immo go rape my eyes.",
    "<KomputerKid> Hey did you know if you type your password in it shows up as stars! *********** See?\n"
    "<JacobGuy7800> mariospro\n"
    "<JacobGuy7800> Wait, DAMMIT",
    "<billy_mccletus> The onlee wuhn whose gunna be marryin' mah sister is gunna be me.",
    "<maxell> He just needs to realize we're one giant schizophrenic cat floating in a void...",
    "<KomputerKid> Why are you gae?",
    "<|> The holy bobble says 'Fuck you'",
    "<psychobat> https://www.youtube.com/watch?v=HqF_nPbX_Ow\n"
    "<Amity> Amity has quit. (Shutting down...)\n"
    "<lily> Amity did not expect the spanish inquisition.",
    "<psychobat> ?quote\n"
    "<psychobat> https://www.youtube.com/watch?v=HqF_nPbX_Ow\n"
    "<Amity> Amity has quit. (Shutting down...)\n"
    "<lily> Amity did not expect the spanish inquisition.\n"
    "<Leo7Mario> Leo7Mario has quit. (Shutting down...)\n"
    "<psychobat> Nor did Leo7Mario.",
]

combined_quotes = tt_quotes + scrape_quotes()

# Quote command. Pulls from quotes above.

@tree.command(name='quote', description='Get a random quote from the old IRC Days')
async def quote(interaction):
    embed = discord.Embed(title="Quote", color=discord.Color.blurple())
    random_quote = random.choice(combined_quotes)
    embed.add_field(name='', value=f"```{random_quote}```", inline=True)
    await interaction.response.send_message(embed=embed)