from api.routes import arxiv, assistant, metadata, paper, search
from arxiv import HTTPError
from arxiv_lib.exceptions import ArxivServiceError, EntityNotFound, ServiceNotAvailable
from celery.result import AsyncResult
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from schemas.metadata import TaskStatusResponse
from services.builders import celery_app

app = FastAPI(
    title="Arxiv Assistant API",
    description="API for searching and querying arXiv papers with RAG and assistant capabilities.",
    version="0.1.0",
)

app.include_router(arxiv.router)
app.include_router(metadata.router)
app.include_router(paper.router)
app.include_router(search.router)
app.include_router(assistant.router)


@app.exception_handler(ArxivServiceError)
def arxiv_error_handler(request, exc):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, EntityNotFound):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, HTTPError):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    elif isinstance(exc, ServiceNotAvailable):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    task_status = TaskStatusResponse(
        task_id=task_id,
        status=result.state,
        result=result.result if result.ready() else None,
    )
    return task_status
