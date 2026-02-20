from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime
from arxiv_lib.db_models.enums import UserRoles


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: UserRoles
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None
