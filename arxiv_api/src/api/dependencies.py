from arxiv_lib.repositories.paper import PaperRepository
from arxiv_lib.db_models import models
from arxiv_lib.db_models.enums import UserRoles
from typing import Annotated
from assistant.main import ArxivAssistant
from api.core.db import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from services.builders import celery_client, openai_client, vector_db_client
from services.search import SearchEngineService
from services.tasks import TaskService
from sqlalchemy.orm import Session
from schemas.user import TokenPayload, UserOut
from api.core import security
from config import settings
import jwt


oauth2_schema = OAuth2PasswordBearer(
    tokenUrl="login"
)

SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_schema)]


def get_current_user(session: SessionDep, token: TokenDep) -> UserOut:
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
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
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_paper_repo(
    db: SessionDep,
) -> PaperRepository:
    return PaperRepository(db)


def get_task_service(
    db: SessionDep,
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
    paper_repo: PaperRepository = Depends(get_paper_repo)
) -> ArxivAssistant:
    return ArxivAssistant(
        search_engine=search_engine,
        paper_repo=paper_repo,
        client=openai_client,
    )
