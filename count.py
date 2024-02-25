import logging
import discord
from discord.ext import commands, tasks

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(intents=intents)

counting_channel_id = 1211195326363336765  # Replace with the ID of your counting channel
debug_channel_id = 1196711795906318437    # Replace with the ID of your debug channel
target_number = 0

@bot.slash_command(name='count', description='Start a counting game', guild_ids=[...])
async def count(interaction, number: int):
    global target_number
    target_number = number
    embed = discord.Embed(title="Counting Game", color=discord.Color.blurple())
    embed.add_field(name="Instructions", value=f"Let's count to {target_number:,}! Start from 1.", inline=False)
    await interaction.response.send_message(content="@here", embed=embed)


@bot.event
async def on_message(message):
    global target_number
    if message.author == bot.user:
        return

    if message.channel.id == counting_channel_id or debug_channel_id:
        try:
            count = int(message.content)
            if count == target_number:
                message.channel.send(f'Congratulations! We\'ve reached {target_number:,}!')
                return
            elif count != 1 and count != int(message.reference.cached_message.content) + 1:
                message.channel.send(f'FUCK! {message.author.mention} Screwed up! Let\'s start over from 1!')
                return
        except ValueError:
            pass

    await bot.process_commands(message)


@count.error
async def count_error(ctx, error):
    if isinstance(error, commands.BadUnionArgument):
        await ctx.interaction.response.send_message('Please enter a valid number to count to.', ephemeral=True)
