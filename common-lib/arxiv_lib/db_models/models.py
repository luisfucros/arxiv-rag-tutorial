import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy
from sqlalchemy import JSON, UUID, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.databases.postgresql import Base
from .enums import TaskStatus, UserRoles


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRoles] = mapped_column(Enum(UserRoles), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (sqlalchemy.Index("users_email_unique_id", "email", unique=True),)

    tasks: Mapped[List["ArxivTask"]] = relationship(back_populates="owner")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.full_name!r}, email={self.email!r})"


class Paper(Base):
    __tablename__ = "papers"

    # Core arXiv metadata
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    arxiv_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    categories: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    published_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pdf_url: Mapped[str] = mapped_column(String, nullable=False)

    # Parsed PDF content
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sections: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    references: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    # PDF processing metadata
    parser_used: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parser_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    pdf_processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    pdf_processing_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ArxivTask(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    task_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.pending,
        nullable=False,
    )

    task_type: Mapped[str] = mapped_column(String, nullable=False)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    error_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User"] = relationship(back_populates="tasks")

    __table_args__ = (sqlalchemy.Index("arxiv_task_task_id_unique_id", "task_id", unique=True),)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    owner_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String, nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
