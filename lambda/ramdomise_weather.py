from os import environ as ENV
import random
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import discord
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = ENV["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = discord.Client(intents=intents)


async def assign_weather_and_create_events():
    try:
        conn = psycopg2.connect(
            dbname=ENV['HOSTED_DB_NAME'],
            user=ENV['HOSTED_DB_USER'],
            password=ENV['HOSTED_DB_PASSWORD'],
            host=ENV['HOSTED_DB_HOST'],
            port=ENV['HOSTED_PORT'],
            cursor_factory=RealDictCursor
        )

        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT weather_id, weather_name FROM weather;")
                weathers = cursor.fetchall()

                cursor.execute("""
                    SELECT location_id, location_name, channel_id, server_id
                    FROM location;
                """)
                locations = cursor.fetchall()

                cursor.execute("DELETE FROM weather_assignment;")

                for location_id, location_name, channel_id, server_id in locations:
                    weather_id, weather_name = random.choice(weathers)

                    cursor.execute(
                        "INSERT INTO weather_assignment (location_id, weather_id) VALUES (%s, %s);",
                        (location_id, weather_id)
                    )

                    guild = bot.get_guild(server_id)
                    if guild is None:
                        print(f"Guild {server_id} not found.")
                        continue

                    channel = guild.get_channel(channel_id)
                    if channel is None:
                        print(
                            f"Channel {channel_id} not found in guild {server_id}.")
                        continue

                    start_time = datetime.now(timezone.utc)
                    end_time = start_time + timedelta(hours=24)
                    event_name = f"{weather_name} in {location_name}"
                    description = f"Today's weather in **{location_name}** is **{weather_name}**."

                    try:
                        await guild.create_scheduled_event(
                            name=event_name,
                            description=description,
                            start_time=start_time,
                            end_time=end_time,
                            channel=channel,
                            entity_type=discord.EntityType.external
                        )
                        print(f"✅ Event created: {event_name}")
                    except Exception as e:
                        print(f"❌ Failed to create event: {e}")

        conn.close()
    except Exception as e:
        print(e)


@bot.event
async def on_ready():
    print("Bot is ready")
    try:
        await assign_weather_and_create_events()
    except Exception as e:
        print(e)
    await bot.close()
    await bot.http._HTTPClient__session.close()  # Close aiohttp connector
    await asyncio.sleep(1)  # Give everything time to shut down



def lambda_handler(event, context):
    asyncio.run(DISCORD_TOKEN)


if __name__ == "__main__":
    lambda_handler(None, None)