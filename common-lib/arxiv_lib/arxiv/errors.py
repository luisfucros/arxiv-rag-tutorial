import functools
import logging

from arxiv import HTTPError
from requests.exceptions import ConnectionError

from ..exceptions import FileError, ServiceNotAvailable

logger = logging.getLogger(__name__)


def handle_errors(func):
    """
    Handle Arxiv client errors, log them, and raise them.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            logger.error(
                "HTTPError during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise
        except (ConnectionError, TimeoutError) as e:
            logger.error(
                "Arxiv service error during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise ServiceNotAvailable("Arxiv service not available")
        except (FileNotFoundError, IOError, OSError) as e:
            logger.error(
                "File error during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise FileError("File error occurred while handling pdf")
        except Exception as e:
            logger.error(
                "Arxiv error during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise

    return wrapper  # type: ignore[return-value]
