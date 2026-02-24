import uuid
from typing import Any, Dict, List, Optional

from arxiv_lib.db_models.enums import TaskStatus
from arxiv_lib.db_models.models import ArxivTask
from arxiv_lib.exceptions import ConflictError, EntityNotFound
from sqlalchemy.orm import Session


class TaskRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, task_name: str, parameters: Dict[str, Any], owner_id: int) -> ArxivTask:
        task = ArxivTask(
            task_id=str(uuid.uuid4()), task_type=task_name, parameters=parameters, owner_id=owner_id
        )
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_tasks(self, limit: int = 100, offset: int = 0) -> List[ArxivTask]:
        """Return a list of tasks ordered by newest first."""
        return (
            self.session.query(ArxivTask)
            .order_by(ArxivTask.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_task(self, task_id: str) -> Optional[ArxivTask]:
        """Return a single task by its `task_id`, or `None` if not found."""
        return self.session.query(ArxivTask).filter_by(task_id=task_id).one_or_none()

    def reset_task(self, task_id: str) -> ArxivTask:
        """Reset a failed task back to pending. Raises ValueError if not found or not failed.

        This clears `error_type` and `error_message` and sets `status` to `pending`.
        """
        task = self.get_task(task_id)
        if not task:
            raise EntityNotFound(f"task with id {task_id} not found")
        if task.status != TaskStatus.failed:
            raise ConflictError("only failed tasks can be reset")

        task.status = TaskStatus.pending
        task.error_type = None
        task.error_message = None
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
