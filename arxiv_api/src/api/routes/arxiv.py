from typing import List

from api.handlers.instances import arxiv_client
from arxiv_lib.schemas import ArxivPaper
from schemas import PaperRequest
from config import settings
from fastapi import APIRouter

router = APIRouter(prefix="/arxiv", tags=["Arxiv"])

@router.post("/search-paper", response_model=List[ArxivPaper])
def search_paper(paper_request: PaperRequest):
    papers = arxiv_client.search_papers(query=paper_request.query, max_results=settings.arxiv.max_results)
    return papers


@router.get("/search-paper/{arxiv_id}", response_model=ArxivPaper)
def get_paper(arxiv_id: str):
    paper, _ = arxiv_client.get_by_id(arxiv_id=arxiv_id)
    return paper
