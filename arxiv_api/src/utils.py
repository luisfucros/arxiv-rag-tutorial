from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError

from api.core import security
from config import settings
from arxiv_lib.db_models.models import Paper


def paper_to_dict(paper: Paper) -> dict:
    return {
        "id": str(paper.id),
        "arxiv_id": paper.arxiv_id,
        "title": paper.title,
        "published_date": paper.published_date.isoformat() if paper.published_date else None,
        "pdf_processed": paper.pdf_processed,
        "pdf_processing_date": (
            paper.pdf_processing_date.isoformat()
            if paper.pdf_processing_date else None
        )
    }


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
