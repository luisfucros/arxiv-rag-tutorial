from enum import StrEnum


class TaskNames(StrEnum):
    """
    Names of Celery tasks registered.
    """
    metadata_fetcher_task = "metadata_fetcher_task"
    embeddings_dense = "embeddings_dense"
    embeddings_sparse = "embeddings_sparse"
