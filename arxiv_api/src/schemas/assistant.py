from pydantic import BaseModel
from typing import Dict, List


class ChatHistoryRequest(BaseModel):
    chat_history: List[Dict[str, str]]


class ChatResponse(BaseModel):
    answer: str
