from api.dependencies import get_paper_repo
from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.schemas import PaperResponse, PaperSearchResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status
from api.dependencies import get_current_user


router = APIRouter(prefix="/paper", tags=["Paper"], dependencies=[Depends(get_current_user)])


@router.get("/{arxiv_id}", response_model=PaperResponse)
def get_paper(arxiv_id: str, paper_repository: PaperRepository = Depends(get_paper_repo)):
    paper = paper_repository.get_by_arxiv_id(arxiv_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Paper not found")
    return paper


@router.get("/", response_model=PaperSearchResponse)
def list_papers(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    paper_repository: PaperRepository = Depends(get_paper_repo),
):
    total = paper_repository.get_count()
    papers = paper_repository.get_all(limit=limit, offset=offset)
    return PaperSearchResponse(papers=papers, total=total)
