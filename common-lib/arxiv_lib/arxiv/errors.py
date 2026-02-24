import functools

from arxiv import HTTPError
from requests.exceptions import ConnectionError

from ..exceptions import ServiceNotAvailable


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError:
            raise
        except (ConnectionError, TimeoutError):
            raise ServiceNotAvailable("Arxiv service not available")
        except (FileNotFoundError, IOError, OSError):
            raise
        except Exception:
            raise

    return wrapper  # type: ignore[return-value]
