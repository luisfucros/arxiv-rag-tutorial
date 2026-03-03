from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str = Field(..., min_length=1, max_length=100_000)

    model_config = ConfigDict(extra="forbid")

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message content cannot be empty")
        return v


class ChatHistoryRequest(BaseModel):
    chat_history: List[ChatMessage] = Field(..., min_length=1, max_length=50)

    model_config = ConfigDict(extra="forbid")

    @field_validator("chat_history")
    @classmethod
    def validate_roles(cls, messages: List[ChatMessage]) -> List[ChatMessage]:
        """
        Security rules:
        - Last message MUST be from user
        - No consecutive assistant messages
        """
        if messages[-1].role != ChatRole.user:
            raise ValueError("Last message must be from user")

        for i in range(1, len(messages)):
            if (
                messages[i].role == ChatRole.assistant
                and messages[i - 1].role == ChatRole.assistant
            ):
                raise ValueError("Consecutive assistant messages not allowed")

        return messages


class ChatResponse(BaseModel):
    answer: str
    message_id: UUID
