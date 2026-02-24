from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=100)
    filters: Optional[Dict[str, str]] = None


class PaperChunk(BaseModel):
    arxiv_id: str = Field(..., description="ArXiv identifier with version")
    chunk_text: str = Field(..., description="Text content of the chunk")

    section_title: str = Field(..., description="Title of the section this chunk belongs to")

    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Comma-separated author list")

    categories: List[str] = Field(..., description="ArXiv subject categories")

    published_date: datetime = Field(..., description="Publication date in ISO format")


class SearchResponse(BaseModel):
    results: List[PaperChunk]
