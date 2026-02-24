from typing import Any, Dict

from arxiv_lib.tasks.enums import TaskNames
from clients.celery_client import CeleryClient
from repositories.tasks import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository, celery_client: CeleryClient):
        self.repository = repository
        self.celery_client = celery_client

    def async_task(self, task_name: TaskNames, params: Dict[str, Any], owner_id: int) -> str:
        log = self.repository.create(task_name, params, owner_id)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs={"params": params},
        )

        return result.task_id

    def run_task(self, task_name: TaskNames, params: Dict[str, Any], owner_id: int) -> Any:
        log = self.repository.create(task_name, params, owner_id)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs={"params": params},
        )

        output = result.get()
        result.forget()  # Clear space on Redis

        return output

    def get_tasks(self, limit: int = 100, offset: int = 0):
        """Return a list of tasks from the repository."""
        return self.repository.get_tasks(limit=limit, offset=offset)

    def get_task(self, task_id: str):
        """Return a single task by `task_id` or `None` if not found."""
        return self.repository.get_task(task_id)

    def retry_task(self, task_id: str):
        """Retry a failed task back to pending via the repository and re-enqueue it.

        Returns the enqueued Celery task id.
        """
        task = self.repository.reset_task(task_id)

        result = self.celery_client.send_task(
            task_name=task.task_type,
            task_id=task.task_id,
            kwargs={"params": task.parameters},
        )

        return result.task_id
