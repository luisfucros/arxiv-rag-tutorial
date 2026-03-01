from ..config import PostgreSQLSettings, get_settings
from .databases.base import BaseDatabase
from .databases.postgresql import PostgreSQLDatabase


def make_database() -> BaseDatabase:
    """Factory function to create a database instance.

    :returns: An instance of the database
    :rtype: BaseDatabase
    """
    # Get settings from centralized config
    settings = get_settings().postgres

    # Create PostgreSQL config from settings
    config = PostgreSQLSettings(
        database_url=settings.database_url,
        echo_sql=settings.echo_sql,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
    )

    database = PostgreSQLDatabase(config=config)
    database.startup()
    return database
