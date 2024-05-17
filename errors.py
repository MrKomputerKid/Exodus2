import discord
import traceback
import sys

async def handle_error(interaction, error):
    """Handles errors raised during command execution."""
    if isinstance(error, discord.errors.CommandNotFound):
        # Command not found error
        embed = discord.Embed(title="Error", description="Command not found.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    # Log the error traceback
    print('Ignoring exception in command:', file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    # Send the error as an embed
    embed = discord.Embed(title="Error", description=f"An error occurred: `{error}`", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

async def on_error(event_method, *args, **kwargs):
    """Handles errors raised during event execution."""
    print('Ignoring exception in', event_method, file=sys.stderr)
    traceback.print_exc()

async def on_command_error(interaction, error):
    """Handles errors raised during command invocation."""
    if hasattr(interaction.data, 'error'):
        return

    # Log the error traceback
    print('Ignoring exception in command:', file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    # Send the error as an embed
    embed = discord.Embed(title="Error", description=f"An error occurred: `{error}`", color=discord.Color.red())
    await interaction.response.send_message(embed=embed)
