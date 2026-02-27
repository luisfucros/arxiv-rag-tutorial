from datetime import datetime
from typing import Optional
from uuid import UUID

from arxiv_lib.db_models.enums import FeedbackValue
from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    message_id: UUID
    value: FeedbackValue
    comment: Optional[str] = None


class FeedbackUpdate(BaseModel):
    value: Optional[FeedbackValue] = None
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: UUID
    user_id: int
    message_id: UUID
    value: FeedbackValue
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
