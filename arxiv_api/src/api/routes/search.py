from api.dependencies import get_search_engine_service
from fastapi import APIRouter, Depends
from schemas.search import SearchRequest, SearchResponse
from services.search import SearchEngineService
from api.dependencies import get_current_user


router = APIRouter(prefix="/search", tags=["Search"], dependencies=[Depends(get_current_user)])


@router.post("/", response_model=SearchResponse)
def search_papers(
    payload: SearchRequest,
    search_engine_service: SearchEngineService = Depends(get_search_engine_service),
):
    results = search_engine_service.search(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    return SearchResponse(results=results)
