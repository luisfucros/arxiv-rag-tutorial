import asyncio
import json
from typing import List

from api.dependencies import get_current_user, get_task_service
from arxiv_lib.tasks.utils import make_json_safe
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from schemas.metadata import TaskResponse, TaskStatusResponse
from services.builders import get_celery_app
from services.tasks import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"], dependencies=[Depends(get_current_user)])


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=get_celery_app)
    task_status = TaskStatusResponse(
        task_id=task_id,
        status=result.state,
        result=result.result if result.ready() else None,
    )
    return task_status


@router.get("/", response_model=List[TaskStatusResponse])
def list_tasks(task_service: TaskService = Depends(get_task_service)):
    tasks = task_service.get_tasks()
    return [TaskStatusResponse(task_id=t.task_id, status=t.status, result=None) for t in tasks]


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task(task_id: str, task_service: TaskService = Depends(get_task_service)):
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"task with id {task_id} not found"
        )
    return TaskStatusResponse(task_id=task.task_id, status=task.status, result=None)


@router.post("/retry/{task_id}", response_model=TaskResponse)
def retry_task(task_id: str, task_service: TaskService = Depends(get_task_service)):
    """Retry a failed task and re-enqueue it. Returns a simple status."""
    celery_id = task_service.retry_task(task_id)

    return TaskResponse(task_id=celery_id, status="requeued")


@router.get("/stream/{task_id}")
async def stream_task_status(
    task_id: str,
    task_service: TaskService = Depends(get_task_service),
    poll_interval: int = 1,
):
    """Stream task status updates via Server-Sent Events (SSE).

    This endpoint connects to a task and streams status updates as they change.
    The stream will close when the task completes (success, failure, or revoked).
    """

    async def event_generator():
        last_status = None
        max_retries = 300
        retry_count = 0

        while retry_count < max_retries:
            try:
                task = task_service.get_task(task_id)
                if not task:
                    yield 'event: error\ndata: {"error": "Task not found"}\n\n'
                    break

                celery_result = AsyncResult(task_id, app=get_celery_app())

                current_status = {
                    "task_id": task.task_id,
                    "status": celery_result.state,
                    "db_status": task.status.value
                    if hasattr(task.status, "value")
                    else str(task.status),
                    "result": celery_result.result if celery_result.ready() else None,
                }

                if current_status != last_status:
                    yield f"data: {json.dumps(current_status, default=make_json_safe)}\n\n"
                    last_status = current_status

                if celery_result.state in ["SUCCESS", "FAILURE", "REVOKED", "REJECTED"]:
                    yield f'event: close\ndata: {{"message": "Task completed with status {celery_result.state}"}}\n\n'
                    break

                # Wait before next poll
                await asyncio.sleep(poll_interval)
                retry_count += 1

            except Exception as exc:
                yield f'event: error\ndata: {{"error": "{str(exc)}"}}\n\n'
                break

        if retry_count >= max_retries:
            yield 'event: timeout\ndata: {"message": "Task monitoring timeout"}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
