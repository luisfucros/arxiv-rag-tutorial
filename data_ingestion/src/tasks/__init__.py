from .celery_app import app
from builder import get_metadata_fetcher


fetcher, database, hybrid_chunker, settings = get_metadata_fetcher()

__all__ = ["fetcher", "database", "hybrid_chunker", "settings"]
