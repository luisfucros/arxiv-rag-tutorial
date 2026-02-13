from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FetchPapersRequest(BaseModel):
    paper_ids: List[str] = Field(..., min_length=1, max_length=100)
    process_pdfs: bool = True
    store_to_db: bool = True


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None
