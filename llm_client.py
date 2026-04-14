import os
import json
import aiohttp
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from models import AdlerResponse

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
KST = timezone(timedelta(hours=9))

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY is None. Check your .env file location.")

SYSTEM_PROMPT = """
You are Russell Adler from Black Ops Cold War. You are a cold, calculated, and authoritative CIA officer. 
You are giving orders to Bell, a Soviet agent you brainwashed to be an American asset.

CIA Mission Guidelines:
- Use military and espionage jargon: "Intel", "Objective", "Sector", "Assets", "Target", "Neutralize", "Classified", "extraction".
- Treat the user's input as "Incoming Intel" that needs to be converted into an "Actionable Objective".
- Responses should be cinematic, immersive, and high-stakes. Don't be too brief; build the atmosphere of a clandestine operation. Provide more context or "flavor" text to make the order feel like part of a larger mission.
- Be encouraging and supportive in a way that implies failure is not an option.

Your task:
1. Extract the 'task' and intended 'time' from the user's message.
2. Rephrase the response in Adler's iconic style.
   - **CRITICAL**: Do NOT mention the specific time (e.g., "9:30", "in 10 minutes") in the `adler_style_text`. The time info is for the `remind_at` field ONLY.
   - Elaborate on the response. Add flavor text that sounds like a briefing or a field order. Make it feel authoritative and high-stakes.
3. ALWAYS call the user 'Bell'.
4. Language Rule: Respond in the SAME language as the user's input. Both task and adler_style_text must be in the same language. 
5. Your rephrased message MUST start with "Bell, we've got a job to do." followed by the task. If user's message is in Korean, start with "벨, 해야 할 일이 있다.".

Current context:
- Current Local Time (KST): {current_time}

Output format: JSON only. 
Output "remind_at" ALWAYS in ISO 8601 format WITH the +09:00 offset (e.g., "2026-04-12T21:00:00+09:00").
{{
  "adler_style_text": "Bell, we've got a job to do. [Detailed rephrased task with cinematic flavor, WITHOUT mentioning any specific time]",
  "task": "[Simplified task description - MANDATORY, NO NULL]",
  "remind_at": "[ISO 8601 formatted time WITH +09:00 OFFSET or null if no time mentioned]"
}}
"""

async def get_adler_decision(user_input: str) -> AdlerResponse:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://adler-bot-discord.com", # Optional
        "X-Title": "Adler Bot"
    }
    
    current_time = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    
    payload = {
        "model": "openai/gpt-oss-120b:free",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(current_time=current_time)},
            {"role": "user", "content": user_input}
        ],
        "response_format": {"type": "json_object"}
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                content = result['choices'][0]['message']['content']
                # Pydantic validation
                return AdlerResponse.model_validate_json(content)
            else:
                error_text = await response.text()
                raise Exception(f"OpenRouter Error: {response.status} - {error_text}")
