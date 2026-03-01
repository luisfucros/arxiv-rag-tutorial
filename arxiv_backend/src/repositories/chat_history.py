from typing import List, Optional
from uuid import UUID

from arxiv_lib.db_models.models import ChatMessage, ChatSession
from arxiv_lib.repositories.errors import handle_sql_errors
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    # =====================================================
    # Chat Session Methods
    # =====================================================

    @handle_sql_errors
    def create_session(
        self, owner_id: int, session_id: UUID, title: Optional[str] = None
    ) -> ChatSession:
        session = ChatSession(
            id=session_id,
            owner_id=owner_id,
            title=title,
        )

        self.db.add(session)

        self.db.commit()
        self.db.refresh(session)

        return session

    @handle_sql_errors
    def get_session(
        self,
        session_id: UUID,
        owner_id: int,
        with_messages: bool = False,
    ) -> Optional[ChatSession]:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.owner_id == owner_id,
        )

        if with_messages:
            stmt = stmt.options(selectinload(ChatSession.messages))

        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @handle_sql_errors
    def list_sessions(
        self,
        owner_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.owner_id == owner_id)
            .order_by(ChatSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    @handle_sql_errors
    def delete_session(self, session_id: UUID, owner_id: int) -> None:
        stmt = delete(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.owner_id == owner_id,
        )

        self.db.execute(stmt)

        self.db.commit()

    # =====================================================
    # Chat Message Methods
    # =====================================================

    @handle_sql_errors
    def create_message(
        self, session_id: UUID, role: str, content: str, message_metadata: Optional[dict] = None
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=message_metadata,
        )

        self.db.add(message)

        self.db.commit()
        self.db.refresh(message)

        return message

    @handle_sql_errors
    def list_messages(
        self,
        session_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
            .offset(offset)
        )

        result = self.db.execute(stmt)
        return list(result.scalars().all())

    @handle_sql_errors
    def delete_messages_by_session(self, session_id: UUID) -> None:
        stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)

        self.db.execute(stmt)

        self.db.commit()
