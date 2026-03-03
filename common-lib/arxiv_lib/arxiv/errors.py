import functools

from arxiv import HTTPError
from loguru import logger
from requests.exceptions import ConnectionError

from ..exceptions import FileError, ServiceNotAvailable


def handle_errors(func):
    """
    Handle Arxiv client errors, log them, and raise them.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as e:
            logger.opt(exception=True).error(
                "HTTPError during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise
        except (ConnectionError, TimeoutError) as e:
            logger.opt(exception=True).error(
                "Arxiv service error during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise ServiceNotAvailable("Arxiv service not available")
        except (FileNotFoundError, IOError, OSError) as e:
            logger.opt(exception=True).error(
                "File error during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise FileError("File error occurred while handling pdf")
        except Exception as e:
            logger.opt(exception=True).error(
                "Arxiv error during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise

    return wrapper  # type: ignore[return-value]
