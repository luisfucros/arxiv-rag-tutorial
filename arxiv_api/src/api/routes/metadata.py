from fastapi import APIRouter, Depends
from api.dependencies import get_task_service

from schemas.metadata import FetchPapersRequest, TaskResponse
from services.tasks import TaskService

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.post("/fetch", response_model=TaskResponse)
def fetch_and_process_metadata(payload: FetchPapersRequest,
                               task_handler: TaskService = Depends(get_task_service)):

    task = task_handler.async_task(
        "tasks.fetch_and_process_papers",
        {
            "paper_ids": payload.paper_ids,
            "process_pdfs": payload.process_pdfs,
            "store_to_db": payload.store_to_db,
        }
    )

    return TaskResponse(
        task_id=task,
        status="queued",
    )
