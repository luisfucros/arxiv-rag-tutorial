from typing import Dict, List

from pydantic import BaseModel


class ChatHistoryRequest(BaseModel):
    chat_history: List[Dict[str, str]]


class ChatResponse(BaseModel):
    answer: str
