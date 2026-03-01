from typing import Optional
from uuid import UUID

from arxiv_lib.db_models.enums import FeedbackValue
from arxiv_lib.db_models.models import ChatMessage, ChatSession, Feedback
from arxiv_lib.repositories.errors import handle_sql_errors
from sqlalchemy import delete, select
from sqlalchemy.orm import Session


class FeedbackRepository:
    def __init__(self, db: Session):
        self.db = db

    @handle_sql_errors
    def create(
        self,
        user_id: int,
        message_id: UUID,
        value: FeedbackValue,
        comment: Optional[str] = None,
    ) -> Optional[Feedback]:
        """Create feedback for a message. Fails if the message is not in a session owned by the user."""
        message = self._get_message_owned_by_user(message_id, user_id)
        if not message:
            return None

        feedback = Feedback(
            user_id=user_id,
            message_id=message_id,
            value=value,
            comment=comment,
        )
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    @handle_sql_errors
    def get(self, feedback_id: UUID, user_id: int) -> Optional[Feedback]:
        """Get a feedback by id. Returns None if not found or not owned by user."""
        stmt = select(Feedback).where(
            Feedback.id == feedback_id,
            Feedback.user_id == user_id,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @handle_sql_errors
    def get_by_message(self, message_id: UUID, user_id: int) -> Optional[Feedback]:
        """Get the current user's feedback for a message, if any."""
        message = self._get_message_owned_by_user(message_id, user_id)
        if not message:
            return None

        stmt = select(Feedback).where(
            Feedback.message_id == message_id,
            Feedback.user_id == user_id,
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    @handle_sql_errors
    def update(
        self,
        feedback_id: UUID,
        user_id: int,
        *,
        value: Optional[FeedbackValue] = None,
        comment: Optional[str] = None,
    ) -> Optional[Feedback]:
        """Update feedback by id. Returns updated feedback or None if not found or not owned by user."""
        feedback = self.get(feedback_id, user_id)
        if not feedback:
            return None

        if value is not None:
            feedback.value = value
        if comment is not None:
            feedback.comment = comment

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    @handle_sql_errors
    def delete(self, feedback_id: UUID, user_id: int) -> bool:
        """Delete feedback by id. Returns True if deleted, False if not found or not owned by user."""
        stmt = delete(Feedback).where(
            Feedback.id == feedback_id,
            Feedback.user_id == user_id,
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0

    def _get_message_owned_by_user(self, message_id: UUID, user_id: int) -> Optional[ChatMessage]:
        """Return the message if it belongs to a session owned by the user."""
        stmt = (
            select(ChatMessage)
            .join(ChatSession, ChatMessage.session_id == ChatSession.id)
            .where(
                ChatMessage.id == message_id,
                ChatSession.owner_id == user_id,
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()
