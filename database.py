import os
from supabase import acreate_client, AsyncClient
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class Database:
    def __init__(self):
        self.client: AsyncClient = None

    async def connect(self):
        if not self.client:
            self.client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)

    async def add_reminder(self, user_id: str, channel_id: str, task: str, original_text: str, adler_message: str, remind_at: str = None):
        await self.connect()
        data = {
            "user_id": user_id,
            "channel_id": channel_id,
            "task": task,
            "original_text": original_text,
            "adler_message": adler_message,
            "remind_at": remind_at,
            "is_sent": False if remind_at else True
        }
        return await self.client.table("planner").insert(data).execute()

    async def get_due_planner(self):
        await self.connect()
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        
        # Get planner where remind_at <= now and is_sent is false
        response = await self.client.table("planner") \
            .select("*") \
            .lte("remind_at", now) \
            .eq("is_sent", False) \
            .execute()
        return response.data

    async def mark_as_sent(self, reminder_id: int):
        await self.connect()
        return await self.client.table("planner") \
            .update({"is_sent": True}) \
            .eq("id", reminder_id) \
            .execute()

db = Database()
