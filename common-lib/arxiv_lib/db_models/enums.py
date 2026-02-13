from enum import StrEnum


class TaskStatus(StrEnum):
    """
    Supported job statuses.
    """
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
