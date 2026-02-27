"""add feedback table

Revision ID: a06c5e922d7f
Revises: 850161f7bc56
Create Date: 2026-02-26 19:05:47.724645

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a06c5e922d7f"
down_revision: Union[str, Sequence[str], None] = "850161f7bc56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "feedback",
        sa.Column("id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("message_id", sa.UUID(), autoincrement=False, nullable=False),
        sa.Column(
            "value",
            postgresql.ENUM("positive", "negative", name="feedback_value_enum"),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("comment", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("feedback_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            name=op.f("feedback_message_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("feedback_pkey")),
        sa.UniqueConstraint(
            "user_id",
            "message_id",
            name="feedback_user_message_unique",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("feedback")
    op.execute("DROP TYPE feedback_value_enum")
