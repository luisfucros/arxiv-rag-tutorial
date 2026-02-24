import logging

from api.routes import arxiv, assistant, login, metadata, paper, search, tasks, users
from arxiv import HTTPError
from arxiv_lib.exceptions import (
    ArxivServiceError,
    ConflictError,
    EntityAlreadyExists,
    EntityNotFound,
    ServiceNotAvailable,
)
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Arxiv Assistant API",
    description="API for searching and querying arXiv papers with RAG and assistant capabilities.",
    version="0.1.0",
)

app.include_router(tasks.router)
app.include_router(arxiv.router)
app.include_router(metadata.router)
app.include_router(paper.router)
app.include_router(search.router)
app.include_router(assistant.router)
app.include_router(login.router)
app.include_router(users.router)


@app.exception_handler(ArxivServiceError)
def arxiv_error_handler(request, exc):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, EntityNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, (EntityAlreadyExists, ConflictError)):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, HTTPError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ServiceNotAvailable):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    logger.error("ArxivError [%s]: %s", type(exc).__name__, str(exc), exc_info=True)

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


@app.on_event("startup")
async def startup_event():
    logger.info("Arxiv Assistant API starting up")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Arxiv Assistant API shutting down")


@app.get("/health")
def health():
    return {"status": "ok"}
