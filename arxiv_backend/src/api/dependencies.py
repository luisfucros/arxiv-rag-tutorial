from typing import Annotated

import jwt
from api.core.db import get_db
from api.handlers.instances import get_redis_client
from arxiv_lib.db_models import models
from arxiv_lib.db_models.enums import UserRoles
from arxiv_lib.repositories.paper import PaperRepository
from config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from repositories.chat_history import ChatRepository
from repositories.tasks import TaskRepository
from schemas.user import TokenPayload, UserOut
from services.assistant.client import ArxivAssistant
from services.builders import (
    get_celery_client,
    get_openai_client,
    get_vector_db_client,
)
from services.cache import CacheClient
from services.search import SearchEngineService
from services.tasks import TaskService
from sqlalchemy.orm import Session

oauth2_schema = OAuth2PasswordBearer(tokenUrl="login")

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_schema)]


def get_current_user(session: SessionDep, token: TokenDep) -> UserOut:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.query(models.User).filter(models.User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


CurrentUser = Annotated[UserOut, Depends(get_current_user)]


def get_current_admin(current_user: CurrentUser) -> UserOut:
    if current_user.role != UserRoles.admin:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user


def get_cache(
    client=Depends(get_redis_client),
) -> CacheClient:
    return CacheClient(redis_client=client, settings=settings.redis)


def get_paper_repo(
    db: SessionDep,
) -> PaperRepository:
    return PaperRepository(db)


def get_chat_repo(
    db: SessionDep,
) -> ChatRepository:
    return ChatRepository(db)


def get_task_repo(
    db: SessionDep,
) -> TaskRepository:
    return TaskRepository(db)


def get_task_service(
    task_repository: TaskRepository = Depends(get_task_repo),
) -> TaskService:
    return TaskService(task_repository, get_celery_client())


def get_search_engine_service(
    task_service: TaskService = Depends(get_task_service),
) -> SearchEngineService:
    return SearchEngineService(
        task_manager=task_service,
        vector_db_client=get_vector_db_client(),
    )


def get_arxiv_assistant(
    search_engine: SearchEngineService = Depends(get_search_engine_service),
    paper_repo: PaperRepository = Depends(get_paper_repo),
    chat_repo: ChatRepository = Depends(get_chat_repo),
    cache: CacheClient = Depends(get_cache),
) -> ArxivAssistant:
    return ArxivAssistant(
        search_engine=search_engine,
        chat_repo=chat_repo,
        paper_repo=paper_repo,
        client=get_openai_client(),
        # cache=cache
    )
