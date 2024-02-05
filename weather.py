import discord
import random
import aiohttp
import aiomysql
import logging
import re
import asyncio
import os
import sys
import json
import urllib.parse
import dotenv
from discord import app_commands
from discord.ext import tasks, commands
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
    connection = await pool.acquire()
    return pool, connection

openweathermap_api_key = os.getenv('OPENWEATHERMAP_API_KEY')
opencage_api_key = os.getenv('OPENCAGE_API_KEY')

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
        
class GeocodingService:
    async def get_coordinates(self, location):
        # Use the geocoding service to get the coordinates of the location
        coordinates = await self.fetch_coordinates_from_opencage(location)

        # Check if coordinates were obtained
        if coordinates:
            # Extract latitude and longitude
            latitude, longitude = coordinates

            # Use the weather service to get weather information
            weather_info = await weather_service.get_weather(latitude, longitude, location)

            # Check if weather information was obtained
            if weather_info:
                return weather_info
            else:
                return "Unable to fetch weather information."
        else:
            return "Unable to determine coordinates for the location."

    async def fetch_coordinates_from_opencage(self, location):
        geocoder = OpenCageGeocode(opencage_api_key)
        try:
            results = geocoder.geocode(location)

            if results and 'geometry' in results[0]:
                geometry = results[0]['geometry']
                return geometry['lat'], geometry['lng']
            else:
                print(f"No results found in OpenCage response for {location}")
            return None
        except Exception as e:
            print(f"Error in OpenCage API request: {e}")
        return None

class WeatherService:
    async def get_weather(self, latitude, longitude, location):
        # Use the geocoding service to get the coordinates of the location
        coordinates = await geocoding_service.fetch_coordinates_from_opencage(location)

        # Check if coordinates were obtained
        if coordinates:
            return coordinates  # Return the obtained coordinates
        else:
            return None

# Create instances of your services
geocoding_service = GeocodingService()
weather_service = WeatherService()

# Weather command! Fetch the weather!
@tree.command(name="weather", description="Fetch the weather!")
async def weather(interaction, location: str = None, unit: str = None):
    state_province = ''
    country = ''
    def filter_geonames(results):
        return [
            result for result in results
            if result['components']['_category'] == 'place'
            and result['components']['_type'] == 'city'
        ]

    async def get_city_details(location):
        geocoder = OpenCageGeocode(opencage_api_key)
        try:
            await interaction.response.defer()
            results = geocoder.geocode(location)
            print(f"OpenCage Response for {location}: {results}")

            results = filter_geonames(results)

            if results and 'components' in results[0]:
                components = results[0]['components']
                print(f"components: {components}")
                state_province = components.get('state') or components.get('state_code') or components.get('state_district') or ''
                country = components.get('country') or components.get('country_code') or ''

                print(f"DEBUG: state_province: {state_province}, country: {country}")

                # Return a dictionary with location information
                return {
                    'city': components.get('place'), 
                    'state_province': state_province, 
                    'country': country,
                    'lng': results[0]['geometry']['lng'],
                    'lat': results[0]['geometry']['lat']
                }
            else:
                print(f"No results found in OpenCage response for {city}")
                return {}
        except Exception as e:
            print(f"Error in OpenCage API request: {e}")
        return {}

    async def get_weather_info(latitude, longitude):
        # Use the weather service to get weather information
        weather_info = await weather_service.get_weather(latitude, longitude, location)
        return weather_info

    async with aiohttp.ClientSession() as session:
        # Connect to the database
        pool, connection = await connect_to_db()

        try:
            # If unit is not provided, retrieve the user's preferred unit from the database
            unit = await get_user_unit(interaction.user.id, pool)
            print(f"DEBUG: Unit retrieved from the database: {unit}")

            if not unit:
                # Default to Celsius if the unit is not provided and there is no unit in the database.
                unit = 'C'

            # Check if the location is not provided
            if location is None:
                # Retrieve the user's location from the database
                location = await get_user_location(interaction.user.id, pool)
                print(f"DEBUG: Location retrieved from the database: {location}")

                if not location:
                    await interaction.response.send_message('Please specify a location or set your location using the `setlocation` command.')
                    return

        finally:
            # Release the database connection
            await pool.release(connection)

            # Split the input into parts (city, state_province, country)
            location_parts = [part.strip() for part in location.split(',')]

            # Assign values based on the number of parts provided
            city = location_parts[0]
            state_province = location_parts[1] if state_province is None and len(location_parts) > 1 else ''
            country = location_parts[2] if country is None and len(location_parts) > 2 else ''

            # Use OpenCage to get state_province and country details.
            city_details = await get_city_details(f'{city} {state_province} {country}')
            state_province_cage = city_details.get('state_province', '')
            country_cage = city_details.get('country', '')

            state_province = state_province or state_province_cage or ''
            country = country_cage or country or ''

            # Construct the full location string without extra commas
            full_location = ', '.join(part for part in [city, state_province, country] if part)

            # Use the geocoding service to get coordinates
            coordinates = (city_details.get('lat'), city_details.get('lng'))

        # Check if coordinates were obtained
        if coordinates:
            # Extract latitude and longitude
            latitude, longitude = coordinates

            # Use the weather service to get weather information
            weather_info = await get_weather_info(latitude, longitude)

    async with aiohttp.ClientSession() as session:
        try:
            url = f'http://api.openweathermap.org/data/2.5/weather?q={full_location}&appid={openweathermap_api_key}&units=metric'
            print(f"DEBUG: OpenWeatherMap API URL: {url}")

            async with session.get(url) as response:
                data = await response.json()

                print(f"DEBUG: OpenWeatherMap API Response: {data}")

            if data and data.get('cod') == 200:
                temp_celsius = data['main']['temp']
                description = data['weather'][0]['description']

                # Convert temperature based on the user's preferred unit
                if unit == 'F':
                    temp_fahrenheit = temp_celsius * 9/5 + 32
                    await interaction.followup.send(f'The current temperature in {full_location} is {temp_fahrenheit:.1f}°F with {description}.')
                elif unit == 'K':
                    temp_kelvin = temp_celsius + 273.15
                    await interaction.followup.send(f'The current temperature in {full_location} is {temp_kelvin:.2f}°K with {description}.')
                else:
                    await interaction.followup.send(f'The current temperature in {full_location} is {temp_celsius}°C with {description}.')
            else:
                await interaction.followup.send(f'The current weather in {full_location} is {weather_info}.')

        except Exception as e:
            error_message = f"Error in weather command: {e}"
            print(error_message)
            await interaction.followup.send(f"An error occurred while handling the weather command: {e}")

# Setlocation command.
            
# Sets a location and stores this information in a mariadb database.

@tree.command(name='setlocation', description='Set your preferred location')
async def setlocation(interaction, location: str, state_province: str = None, country: str = None):
    pool, connection = await connect_to_db()

    # Check if the user's location is already set to the provided location
    current_location = await get_user_location(interaction.user.id, pool)
    if current_location == f"{location}, {state_province}, {country}" or current_location == f"{location}, {country}":
        await pool.release(connection)
        await interaction.response.send_message('Your location is already set to this location.')
        return

    full_location = f"{location}, {state_province}, {country}" if state_province else f"{location}, {country}"
    await set_user_location(interaction.user.id, full_location, pool)
    await pool.release(connection)
    await interaction.response.send_message(f'Your location has been set to {location}.')

# Setunit command

# Set preferred units for the weather command. Stores this information in a mariadb database.

@tree.command(name='setunit', description='Set your preferred units')
async def setunit(interaction, *, unit: str):
    valid_units = ['C', 'F', 'K']
    
    # Check if the provided unit is valid
    if unit.upper() not in valid_units:
        await interaction.response.send_message('Invalid unit. Please specify either `C` for Celsius, `F` for Fahrenheit, or `K` for Kelvin.')
        return

    pool, connection = await connect_to_db()

    # Check if the user's preferred unit is already set to the specified unit
    current_unit = await get_user_unit(interaction.user.id, pool)
    if current_unit == unit.upper():
        await pool.release(connection)
        await interaction.response.send_message(f'Your preferred temperature unit is already set to {unit.upper()}.')
        return

    await set_user_unit(interaction.user.id, unit.upper(), pool)
    await pool.release(connection)
    await interaction.response.send_message(f'Your preferred temperature unit has been set to {unit.upper()}.')