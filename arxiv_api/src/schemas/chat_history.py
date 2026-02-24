from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChatMessageBase(BaseModel):
    role: str
    content: str
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    session_id: UUID


class ChatMessageResponse(ChatMessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionBase(BaseModel):
    title: Optional[str] = None


class ChatSessionCreate(ChatSessionBase):
    pass


class ChatSessionResponse(ChatSessionBase):
    id: UUID
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessages(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []
