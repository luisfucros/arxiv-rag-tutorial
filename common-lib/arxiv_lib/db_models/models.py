import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import JSON, Boolean, DateTime, String, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import UUID
from ..db.databases.postgresql import Base
from .enums import TaskStatus


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
