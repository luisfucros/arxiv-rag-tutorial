import functools
import logging

import openai
from arxiv_lib.exceptions import RateLimitExceeded, ServiceNotAvailable

logger = logging.getLogger(__name__)


def handle_openai_errors(func):
    """
    Handle OpenAI errors, log them, and raise them.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError) as e:
            logger.error(
                "%s during '%s' [%s.%s]: %s",
                type(e).__name__,
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise ServiceNotAvailable("OpenAI service not available")
        except openai.RateLimitError as e:
            logger.error(
                "RateLimitError during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise RateLimitExceeded("OpenAI service rate limit exceeded")

    return wrapper  # type: ignore[return-value]
