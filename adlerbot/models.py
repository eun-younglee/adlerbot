from pydantic import BaseModel, Field
from typing import Optional

class AdlerResponse(BaseModel):
    adler_style_text: str = Field(description="Adler's response in the same language as the user input")
    task: str = Field(default="Mission details pending", description="The extracted task description")
    remind_at: Optional[str] = Field(None, description="ISO 8601 formatted datetime string, or null if no time is mentioned")
