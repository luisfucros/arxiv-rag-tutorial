from builder import get_services

from .celery_app import app  # type: ignore

fetcher, database, hybrid_chunker = get_services()

__all__ = ["app", "fetcher", "database", "hybrid_chunker"]
