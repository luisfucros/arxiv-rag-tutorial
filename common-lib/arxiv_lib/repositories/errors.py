import functools
import logging

from sqlalchemy.exc import SQLAlchemyError

from ..exceptions import DataBaseError

logger = logging.getLogger(__name__)


def handle_sql_errors(func):
    """
    Handle SQLAlchemy errors, log them, and raise DataBaseError.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(
                "SQLAlchemyError during '%s' [%s.%s]: %s",
                func.__name__,
                type(e).__module__,
                type(e).__qualname__,
                str(e),
                exc_info=True,
            )
            raise DataBaseError(
                "Operation failed '%s' due to DB error: %s" % (func.__name__, type(e).__name__)
            ) from e

    return wrapper  # type: ignore[return-value]
