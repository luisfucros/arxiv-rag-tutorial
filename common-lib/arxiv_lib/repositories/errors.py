import functools

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from ..exceptions import DataBaseError


def handle_sql_errors(func):
    """
    Handle SQLAlchemy errors, log them, and raise DataBaseError.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.opt(exception=True).error(
                "SQLAlchemyError during '{}' [{}.{}]: {}",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
            )
            raise DataBaseError(
                "Operation failed '%s' due to DB error: %s" % (func.__name__, type(e).__name__)
            ) from e

    return wrapper  # type: ignore[return-value]
