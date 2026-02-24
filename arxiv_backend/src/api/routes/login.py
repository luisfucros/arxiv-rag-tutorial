from datetime import timedelta
from typing import Annotated

from api.core import security
from api.dependencies import SessionDep
from arxiv_lib.db_models import models
from config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import Token

router = APIRouter(tags=["login"])


@router.post("/login/")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = session.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect email or password"
        )

    verified, updated_password_hash = security.verify_password(form_data.password, user.password)
    if not verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    if updated_password_hash:
        user.hashed_password = updated_password_hash
        session.add(user)
        session.commit()
        session.refresh(user)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return Token(
        access_token=security.create_access_token(user.id, expires_delta=access_token_expires)
    )
