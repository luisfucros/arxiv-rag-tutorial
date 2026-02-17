import logging
from api.dependencies import get_paper_repo
from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.schemas import PaperResponse, PaperSearchResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/paper", tags=["Paper"])


@router.get("/{arxiv_id}", response_model=PaperResponse)
def get_paper(arxiv_id: str, paper_repository: PaperRepository = Depends(get_paper_repo)):
    logger.info("Fetching paper with arxiv_id: %s", arxiv_id)
    paper = paper_repository.get_by_arxiv_id(arxiv_id)
    if not paper:
        logger.warning("Paper not found for arxiv_id: %s", arxiv_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Paper not found")
    return paper


@router.get("/", response_model=PaperSearchResponse)
def list_papers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    paper_repository: PaperRepository = Depends(get_paper_repo),
):
    logger.info("Listing papers with limit=%d, offset=%d", limit, offset)
    total = paper_repository.get_count()
    papers = paper_repository.get_all(limit=limit, offset=offset)
    logger.info("Retrieved %d papers from total %d", len(papers), total)
    return PaperSearchResponse(papers=papers, total=total)
