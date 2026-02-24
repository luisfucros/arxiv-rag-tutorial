import logging
from typing import List

from api.dependencies import get_current_user
from api.handlers.instances import get_arxiv_client
from arxiv_lib.schemas import ArxivPaper
from config import settings
from fastapi import APIRouter, Depends
from schemas.arxiv import PaperRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/arxiv", tags=["Arxiv"], dependencies=[Depends(get_current_user)])


@router.post("/search-paper", response_model=List[ArxivPaper])
def search_paper(
    paper_request: PaperRequest,
    arxiv_client=Depends(get_arxiv_client),
):
    logger.info("Searching arXiv for query: %s", paper_request.query)
    papers = arxiv_client.search_papers(
        query=paper_request.query, max_results=settings.arxiv.max_results
    )
    logger.info("Found %d papers for query: %s", len(papers), paper_request.query)
    return papers


@router.get("/search-paper/{arxiv_id}", response_model=ArxivPaper)
def get_paper(
    arxiv_id: str,
    arxiv_client=Depends(get_arxiv_client),
):
    logger.info("Fetching paper from arXiv with id: %s", arxiv_id)
    paper, _ = arxiv_client.get_by_id(arxiv_id=arxiv_id)
    logger.info("Successfully fetched paper: %s", arxiv_id)
    return paper
