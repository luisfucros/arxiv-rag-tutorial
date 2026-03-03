from datetime import datetime, timezone

from arxiv_lib.db_models.enums import TaskStatus
from arxiv_lib.db_models.models import ArxivTask
from arxiv_lib.tasks.utils import make_json_safe
from celery import Task
from loguru import logger
from sqlalchemy import select

from . import database


class BaseTask(Task):
    """
    Base class for all Celery tasks in the service.
    """

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo):
        """
        Log the task failure in the DB.
        """
        err_type = type(exc)
        logger.opt(exception=True).error("Task failed [{}]: {}", task_id, str(exc))
        try:
            with database.get_session() as session:
                query = select(ArxivTask).where(ArxivTask.task_id == task_id)
                job = session.scalar(query)
                job.status = TaskStatus.failed
                job.updated_at = datetime.now(timezone.utc)
                job.error_type = f"{err_type.__module__}.{err_type.__name__}"
                job.error_message = str(exc)

                session.add(job)
                session.commit()

        except Exception as e:
            logger.opt(exception=True).error("Failed to log task failure [{}]", type(e).__name__)

    def on_success(self, retval, task_id, args, kwargs):
        """
        Log the task success in the DB.
        """
        logger.info("Task completed successfully [{}]", task_id)
        try:
            with database.get_session() as session:
                query = select(ArxivTask).where(ArxivTask.task_id == task_id)
                job = session.scalar(query)
                job.status = TaskStatus.completed
                job.updated_at = datetime.now(timezone.utc)
                job.result = make_json_safe(retval)
                if job.error_type:
                    job.error_type = None
                    job.error_message = None

                session.add(job)
                session.commit()

        except Exception as e:
            logger.opt(exception=True).error("Failed to log task success [{}]", type(e).__name__)
