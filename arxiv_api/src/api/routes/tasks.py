import logging
from services.builders import celery_app
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.metadata import TaskStatusResponse, TaskResponse
from celery.result import AsyncResult
from api.dependencies import get_task_service
from services.tasks import TaskService
from typing import List


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    logger.debug("Fetching status for task: %s", task_id)
    result = AsyncResult(task_id, app=celery_app)
    task_status = TaskStatusResponse(
        task_id=task_id,
        status=result.state,
        result=result.result if result.ready() else None,
    )
    logger.debug("Task status: %s", result.state)
    return task_status


@router.get("/", response_model=List[TaskStatusResponse])
def list_tasks(task_service: TaskService = Depends(get_task_service)):
    tasks = task_service.get_tasks()
    return [
        TaskStatusResponse(task_id=t.task_id, status=t.status, result=None)
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task(task_id: str, task_service: TaskService = Depends(get_task_service)):
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"task with id {task_id} not found")
    return TaskStatusResponse(task_id=task.task_id, status=task.status, result=None)


@router.post("/reset/{task_id}", response_model=TaskResponse)
def retry_task(task_id: str, task_service: TaskService = Depends(get_task_service)):
    """Reset a failed task and re-enqueue it. Returns a simple status."""
    celery_id = task_service.retry_task(task_id)

    return TaskResponse(task_id=celery_id, status="requeued")
