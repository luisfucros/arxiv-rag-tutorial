import functools

import openai
from arxiv_lib.exceptions import RateLimitExceeded, ServiceNotAvailable
from loguru import logger


def handle_openai_errors(func):
    """
    Handle OpenAI errors, log them, and raise them.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError) as e:
            logger.opt(exception=True).error(
                "{} during '{}' [{}.{}]: {}",
                type(e).__name__,
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise ServiceNotAvailable("OpenAI service not available")
        except openai.RateLimitError as e:
            logger.opt(exception=True).error(
                "RateLimitError during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise RateLimitExceeded("OpenAI service rate limit exceeded")

    return wrapper  # type: ignore[return-value]
