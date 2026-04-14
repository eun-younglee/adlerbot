import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from llm_client import get_adler_decision
from database import db

load_dotenv()
TOKEN = os.getenv("DISCORD_CLIENT")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Adler is active. Logged in as {client.user}')
    if not check_planner.is_running():
        check_planner.start()

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send("Hello, Bell.")

    # Process !plan command
    if message.content.startswith('!plan '):
        user_input = message.content[6:]
        
        async with message.channel.typing():
            try:
                # Get stylized response and extraction from LLM
                adler_res = await get_adler_decision(user_input)
                
                # Always save to DB for logging
                await db.add_reminder(
                    user_id=str(message.author.id),
                    channel_id=str(message.channel.id),
                    task=adler_res.task,
                    original_text=user_input,
                    adler_message=adler_res.adler_style_text,
                    remind_at=adler_res.remind_at
                )

                if adler_res.remind_at:
                    # Immediate confirmation: Brief task only
                    await message.channel.send(f"**Task Received:** {adler_res.task}\n*(Scheduled for: {adler_res.remind_at})*")
                else:
                    # No time info, just send the stylized response
                    await message.channel.send(adler_res.adler_style_text)
                    
            except Exception as e:
                print(f"Error processing !plan: {e}")
                await message.channel.send("Bell, we've encountered a complication. Check the logs.")

# Background task loop to check for due planner every 60 seconds
@tasks.loop(seconds=60)
async def check_planner():
    try:
        due_planner = await db.get_due_planner()
        for rem in due_planner:
            channel_id = int(rem['channel_id'])
            channel = client.get_channel(channel_id)
            
            # Cache에 없으면 직접 API로 가져오기
            if not channel:
                try:
                    channel = await client.fetch_channel(channel_id)
                except:
                    continue

            if channel:
                user_mention = f"<@{rem['user_id']}>"
                # Send the pre-stylized Adler message stored in the DB
                final_msg = rem.get('adler_message') or f"Bell, we've got a job to do. Time for: {rem['task']}"
                await channel.send(f"{user_mention}\n{final_msg}")
                await db.mark_as_sent(rem['id'])
    except Exception as e:
        print(f"Error in check_planner loop: {e}")

client.run(TOKEN)