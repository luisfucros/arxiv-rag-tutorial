from api.dependencies import get_search_engine_service
from fastapi import APIRouter, Depends
from schemas.search import SearchRequest, SearchResponse
from services.search import SearchEngineService
from api.dependencies import CurrentUser


router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
def search_papers(
    payload: SearchRequest,
    current_user: CurrentUser,
    search_engine_service: SearchEngineService = Depends(get_search_engine_service)
):
    results = search_engine_service.search(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
        user_id=current_user.id
    )
    return SearchResponse(results=results)
