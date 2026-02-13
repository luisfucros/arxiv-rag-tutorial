from arxiv_lib.repositories.paper import PaperRepository
from assistant.main import ArxivAssistant
from database.db import get_db
from fastapi import Depends
from services.builders import celery_client, openai_client, vector_db_client
from services.search import SearchEngineService
from services.tasks import TaskService
from sqlalchemy.orm import Session


def get_paper_repo(
    db: Session = Depends(get_db),
) -> PaperRepository:
    return PaperRepository(db)


def get_task_service(
    db: Session = Depends(get_db),
) -> TaskService:
    return TaskService(db, celery_client)


def get_search_engine_service(
    task_service: TaskService = Depends(get_task_service),
) -> SearchEngineService:
    return SearchEngineService(
        task_manager=task_service,
        vector_db_client=vector_db_client,
    )


def get_arxiv_assistant(
    search_engine: SearchEngineService = Depends(get_search_engine_service),
) -> ArxivAssistant:
    return ArxivAssistant(
        search_engine=search_engine,
        client=openai_client,
    )