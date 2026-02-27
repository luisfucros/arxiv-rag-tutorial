from enum import StrEnum


class UserRoles(StrEnum):
    admin = "admin"
    user = "user"


class TaskStatus(StrEnum):
    """
    Supported job statuses.
    """

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class FeedbackValue(StrEnum):
    """User feedback on a chat message (e.g. thumbs up/down)."""

    positive = "positive"
    negative = "negative"
