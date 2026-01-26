import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConfig:

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "aetos")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "")

    def get_connection_string(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password}"
        )

    def validate(self) -> bool:
        if not self.password:
            logger.error("DB_PASSWORD environment variable not set")
            return False
        return True


def get_connection_string() -> str:
    config = DatabaseConfig()
    if not config.validate():
        raise ValueError("Invalid database configuration")
    return config.get_connection_string()
