from api.core import security
from api.dependencies import SessionDep
from arxiv_lib.db_models import models
from fastapi import APIRouter, HTTPException, status
from schemas.user import UserCreate, UserOut
from sqlalchemy import select

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", response_model=UserOut)
def create_user(user_payload: UserCreate, session: SessionDep):

    existing_user = session.scalars(
        select(models.User).where(models.User.email == user_payload.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")

    user_payload.password = security.get_password_hash(user_payload.password)
    db_obj = models.User(**user_payload.model_dump())
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
