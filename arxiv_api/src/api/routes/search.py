import logging
from api.dependencies import get_search_engine_service
from fastapi import APIRouter, Depends
from schemas.search import SearchRequest, SearchResponse
from services.search import SearchEngineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("/", response_model=SearchResponse)
def search_papers(
    payload: SearchRequest,
    search_engine_service: SearchEngineService = Depends(get_search_engine_service),
):
    logger.info("Search request: query=%s, top_k=%s", payload.query, payload.top_k)
    results = search_engine_service.search(
        query=payload.query,
        top_k=payload.top_k,
        filters=payload.filters,
    )
    logger.info("Search completed with %d results", len(results))
    return SearchResponse(results=results)
