import logging
import discord
from discord import app_commands
from discord.ext import tasks

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix='!', intents=intents)
tree = commands.CommandTree(client)

counting_channel_id = 1211195326363336765  # Replace with the ID of your counting channel
debug_channel_id = 1196711795906318437
target_number = 0

@tree.command(name='count', description='Start a counting game')
async def count(interaction, number: int):
    global target_number
    target_number = number
    embed = discord.Embed(title="Counting Game", color=discord.Color.blurple())
    embed.add_field(name="Instructions", value=f"Let's count to {target_number}! Start from 1.", inline=False)
    await interaction.response.send_message(content="@here", embed=embed)


@client.event
async def on_message(message):
    global target_number
    if message.author == client.user:
        return

    if message.content.startswith('!count'):
        return  # Ignore count commands to prevent conflicts

    if message.channel.id == counting_channel_id or debug_channel_id:
        try:
            count = int(message.content)
            if count == target_number:
                await message.channel.send(f'Congratulations! We\'ve reached {target_number}!')
                return
            elif count != 1 and count != int(message.reference.resolved.content) + 1:
                await message.channel.send(f'FUCK! {message.author.mention} Screwed up! Let\'s start over from 1!')
                return
        except ValueError:
            pass

    await client.process_commands(message)


@count.error
async def count_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Please enter a valid number to count to.')