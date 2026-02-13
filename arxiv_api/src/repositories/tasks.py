from sqlalchemy.orm import Session
from typing import Any, Dict
import uuid
from arxiv_lib.db_models.models import ArxivTask


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task_name: str, parameters: Dict[str, Any]) -> ArxivTask:
        task = ArxivTask(
            task_id=str(uuid.uuid4()),
            task_type=task_name,
            parameters=parameters,
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
