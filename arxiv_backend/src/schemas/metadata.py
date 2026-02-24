from typing import Dict, Optional

from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None
