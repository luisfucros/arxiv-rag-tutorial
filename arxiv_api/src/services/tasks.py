from typing import Any, Dict

from clients.celery_client import CeleryClient
from repositories.tasks import TaskRepository
from sqlalchemy.orm import Session
from arxiv_lib.tasks.enums import TaskNames
from arxiv_lib.tasks.mapping import TASK_PARAMS


class TaskService:
    def __init__(self, session: Session, celery_client: CeleryClient):
        self.repository = TaskRepository(session)
        self.celery_client = celery_client
    
    @staticmethod
    def check_params(task_name: TaskNames, params: Dict[str, Any]) -> bool:
        task_params_type = TASK_PARAMS[task_name]
        if isinstance(params, dict):
            task_params = task_params_type(**params)
        elif not isinstance(params, task_params_type):
            raise TypeError(
                "Parameters must be of type %s" % task_params_type.__name__
            )
        else:
            task_params = params
        return task_params

    def async_task(self, task_name: TaskNames, params: Dict[str, Any]) -> str:
        task_params = self.check_params(task_name, params)
        log = self.repository.create(task_name, task_params)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs=task_params,
        )

        return result.task_id

    def run_task(self, task_name: TaskNames, params: Dict[str, Any]) -> Any:
        task_params = self.check_params(task_name, params)
        log = self.repository.create(task_name, task_params)

        result = self.celery_client.send_task(
            task_name=task_name,
            task_id=log.task_id,
            kwargs=task_params,
        )

        output = result.get()
        result.forget()  # Clear space on Redis

        return output
