import discord
import aiohttp
import aiomysql
import logging
import os
import asyncio
import re
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from opencage.geocoder import OpenCageGeocode

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

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

openweathermap_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
opencage_api_key = os.getenv('OPENCAGE_API_KEY')

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

class GeocodingService:
    async def get_coordinates(self, location):
        coordinates = await self.fetch_coordinates_from_opencage(location)
        return coordinates if coordinates else "Unable to determine coordinates for the location."

    async def fetch_coordinates_from_opencage(self, location):
        geocoder = OpenCageGeocode(opencage_api_key)
        try:
            results = geocoder.geocode(location)
            if results and 'geometry' in results[0]:
                geometry = results[0]['geometry']
                return geometry['lat'], geometry['lng'], results[0]['formatted']
            else:
                print(f"No results found in OpenCage response for {location}")
            return None
        except Exception as e:
            print(f"Error in OpenCage API request: {e}")
            return None

class WeatherService:
    async def get_weather(self, latitude, longitude):
        async with aiohttp.ClientSession() as session:
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': openweathermap_api_key,
                'units': 'metric'  # Default to metric, convert if needed later
            }
            async with session.get("http://api.openweathermap.org/data/2.5/weather", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    weather_info = {
                        'temp': data['main']['temp'],
                        'description': data['weather'][0]['description']
                    }
                    return weather_info
                else:
                    print(f"Failed to get weather data: {resp.status}")
                    return None

geocoding_service = GeocodingService()
weather_service = WeatherService()

# State and province codes
US_STATE_CODES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
    "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

UK_COUNTRY_CODES = {
    "England": "ENG", "Scotland": "SCT", "Wales": "WLS", "Northern Ireland": "NIR"
}

CANADA_PROVINCE_CODES = {
    "Alberta": "AB", "British Columbia": "BC", "Manitoba": "MB", "New Brunswick": "NB",
    "Newfoundland and Labrador": "NL", "Northwest Territories": "NT", "Nova Scotia": "NS",
    "Nunavut": "NU", "Ontario": "ON", "Prince Edward Island": "PE", "Quebec": "QC",
    "Saskatchewan": "SK", "Yukon": "YT"
}

AUSTRALIA_STATE_CODES = {
    "New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD", "Western Australia": "WA",
    "South Australia": "SA", "Tasmania": "TAS", "Australian Capital Territory": "ACT",
    "Northern Territory": "NT"
}

def get_state_province_code(state_or_province, country):
    # If it's already a 2-letter code, return it as is
    if len(state_or_province) == 2 and state_or_province.isupper():
        return state_or_province

    state_or_province = state_or_province.title()  # Capitalize first letter of each word
    country = country.title()  # Capitalize first letter of each word

    if country == "United States":
        return US_STATE_CODES.get(state_or_province)
    elif country == "United Kingdom":
        return UK_COUNTRY_CODES.get(state_or_province)
    elif country == "Canada":
        return CANADA_PROVINCE_CODES.get(state_or_province)
    elif country == "Australia":
        return AUSTRALIA_STATE_CODES.get(state_or_province)
    # Add more countries as needed
    return None

def construct_location_string(formatted_location):
    parts = formatted_location.split(', ')
    
    # Remove any zip codes or postal codes
    parts = [part for part in parts if not re.match(r'^\d{5}(-\d{4})?$', part)]
    
    if len(parts) >= 3:
        city = parts[0]
        country = parts[-1]
        state_or_province = parts[-2]  # Assume the second last part is state/province
        
        # Check if state_or_province is already a known postal code
        if len(state_or_province) == 2 and state_or_province.isupper():
            return f"{city}, {state_or_province}, {country}"
        else:
            # Try to find a postal code for the state/province
            postal_code = get_state_province_code(state_or_province, country)
            if postal_code:
                return f"{city}, {postal_code}, {country}"
            else:
                # If it's not a recognized state/province, it might be a county or other subdivision
                # In this case, we'll just return city and country
                return f"{city}, {country}"
    elif len(parts) == 2:
        city, country = parts
        return f"{city}, {country}"
    else:
        return formatted_location  # Return as-is if we can't parse it

@tree.command(name="weather", description="Fetch the weather!")
async def weather(interaction: discord.Interaction, location: str = None, unit: str = None):
    await interaction.response.defer()  # Defer the interaction to allow for long-running tasks
    pool = await connect_to_db()
    try:
        if unit is None:
            unit = await get_user_unit(interaction.user.id, pool)
            if not unit:
                unit = 'C'

        if location is None:
            location = await get_user_location(interaction.user.id, pool)
            if not location:
                await interaction.followup.send('Please specify a location or set your location using the `setlocation` command.')
                return

        city, state_province, country = process_location(location)
        latitude, longitude, formatted_location = await get_coordinates(city, state_province, country)

        if latitude and longitude:
            weather_info = await weather_service.get_weather(latitude, longitude)
            if weather_info:
                location_string = construct_location_string(formatted_location)
                embed = create_weather_embed(location_string, weather_info, unit)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f'Unable to fetch weather information for {location}.')
        else:
            await interaction.followup.send(f'Unable to determine coordinates for {location}. Please check the location and try again.')
    
    except Exception as e:
        error_message = f"Error in weather command: {e}"
        print(error_message)
        await interaction.followup.send(f"An error occurred while handling the weather command: {e}")
    finally:
        pool.close()
        await pool.wait_closed()

def process_location(location):
    if ',' in location:
        city, rest = location.split(',', 1)
        if len(rest.strip()) == 2:
            state_province = ''
            country = ''
        else:
            state_province, country = rest.strip().split(',', 1)
    else:
        city = location
        state_province = ''
        country = ''
    return city.strip(), state_province.strip(), country.strip()

async def get_coordinates(city, state_province, country):
    city_details = await geocoding_service.fetch_coordinates_from_opencage(f'{city} {state_province} {country}')
    if city_details:
        return city_details[0], city_details[1], city_details[2]
    return None, None, None

def create_weather_embed(location_string, weather_info, unit):
    temperature = weather_info['temp']
    description = weather_info['description']

    if unit == 'F':
        temperature = temperature * 9/5 + 32
        temperature_string = f'{temperature:.1f}°F'
    elif unit == 'K':
        temperature = temperature + 273.15
        temperature_string = f'{temperature:.2f}°K'
    else:
        temperature_string = f'{temperature}°C'

    embed = discord.Embed(
        title=f'Weather in {location_string}',
        description=f'Temperature: {temperature_string}\nDescription: {description}',
        color=0x3498db
    )
    return embed

@tree.command(name='setlocation', description='Set your preferred location')
async def setlocation(interaction: discord.Interaction, location: str = None):
    await interaction.response.send_message("Processing your request...", ephemeral=True)
    
    # Create a task to handle the database operations
    asyncio.create_task(process_setlocation(interaction, location))

async def process_setlocation(interaction: discord.Interaction, location: str):
    pool = await connect_to_db()
    try:
        # Validate the location
        latitude, longitude, formatted_location = await geocoding_service.fetch_coordinates_from_opencage(location)
        if not latitude or not longitude:
            await interaction.edit_original_response(content=f'The location "{location}" is invalid. Please provide a valid location.')
            return

        current_location = await get_user_location(interaction.user.id, pool)
        if current_location == location:
            await interaction.edit_original_response(content='Your location is already set to this location.')
            return

        await set_user_location(interaction.user.id, location, pool)
        await interaction.edit_original_response(content=f'Your location has been set to {formatted_location}.')
    except Exception as e:
        await interaction.edit_original_response(content=f"An error occurred: {str(e)}")
    finally:
        pool.close()
        await pool.wait_closed()

@tree.command(name='setunit', description='Set your preferred units')
async def setunit(interaction: discord.Interaction, *, unit: str):
    await interaction.response.send_message("Processing your request...", ephemeral=True)
    
    # Create a task to handle the database operations
    asyncio.create_task(process_setunit(interaction, unit))

async def process_setunit(interaction: discord.Interaction, unit: str):
    valid_units = ['C', 'F', 'K']
    
    if unit.upper() not in valid_units:
        await interaction.edit_original_response(content='Invalid unit. Please specify either `C` for Celsius, `F` for Fahrenheit, or `K` for Kelvin.')
        return

    pool = await connect_to_db()
    try:
        current_unit = await get_user_unit(interaction.user.id, pool)
        if current_unit == unit.upper():
            await interaction.edit_original_response(content=f'Your preferred temperature unit is already set to {unit.upper()}.')
            return

        await set_user_unit(interaction.user.id, unit.upper(), pool)
        await interaction.edit_original_response(content=f'Your preferred temperature unit has been set to {unit.upper()}.')
    except Exception as e:
        await interaction.edit_original_response(content=f"An error occurred: {str(e)}")
    finally:
        pool.close()
        await pool.wait_closed()