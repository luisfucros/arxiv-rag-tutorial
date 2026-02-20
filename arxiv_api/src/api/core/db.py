from typing import Generator
from sqlalchemy.orm import Session

from arxiv_lib.db.factory import make_database

db = make_database()


def get_db() -> Generator[Session, None, None]:
    with db.get_session() as session:
        yield session
