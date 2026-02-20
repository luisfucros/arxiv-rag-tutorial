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
