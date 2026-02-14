from fastapi import APIRouter, Depends
from api.dependencies import get_task_service

from schemas.metadata import TaskResponse
from arxiv_lib.tasks.schemas import PaperMetadataRequest
from services.tasks import TaskService
from arxiv_lib.tasks.enums import TaskNames


router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.post("/fetch", response_model=TaskResponse)
def fetch_and_process_metadata(payload: PaperMetadataRequest,
                               task_handler: TaskService = Depends(get_task_service)):

    task = task_handler.async_task(
        TaskNames.metadata_fetcher_task,
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
