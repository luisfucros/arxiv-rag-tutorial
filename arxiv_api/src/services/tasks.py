from typing import Any, Dict

from clients.celery_client import CeleryClient
from repositories.tasks import TaskRepository
from sqlalchemy.orm import Session


class TaskService:
    def __init__(self, session: Session, celery_client: CeleryClient):
        self.repository = TaskRepository(session)
        self.celery_client = celery_client

    def async_task(self, task_name: str, task_params: Dict[str, Any]) -> str:
        log = self.repository.create(task_name, task_params)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs=task_params,
        )

        return result.task_id

    def run_task(self, task_name: str, task_params: Dict[str, Any]) -> Any:
        log = self.repository.create(task_name, task_params)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs=task_params,
        )

        output = result.get()
        result.forget()  # Clear space on Redis

        return output
