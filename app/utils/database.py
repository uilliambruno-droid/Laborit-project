import os
from functools import lru_cache
from logging import getLogger

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

_REQUIRED_VARS = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME")
logger = getLogger(__name__)


def _require_env(name: str) -> str:
    """Return env var value or raise immediately — never fall back to a default."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it via .env or your runtime secrets provider."
        )
    return value


def get_database_url() -> str:
    """Build DSN from env vars. Raises RuntimeError if any required var is absent."""
    if database_url := os.getenv("DATABASE_URL"):
        return database_url

    db_user = _require_env("DB_USER")
    db_password = _require_env("DB_PASSWORD")
    db_host = _require_env("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = _require_env("DB_NAME")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def _classify_database_error(error: Exception) -> str:
    message = str(error).lower()

    if any(
        keyword in message for keyword in ("access denied", "authentication", "1045")
    ):
        return "Database authentication failed: verify user and password"

    if any(
        keyword in message for keyword in ("unknown database", "1049", "doesn't exist")
    ):
        return "Database not found: verify database name"

    if any(
        keyword in message
        for keyword in ("can't connect", "cannot connect", "connection refused", "2003")
    ):
        return "Database host unreachable: verify host, port, and network access"

    if any(
        keyword in message
        for keyword in (
            "name or service not known",
            "nodename nor servname",
            "temporary failure in name resolution",
        )
    ):
        return "Database host resolution failed: verify host value"

    if "timed out" in message:
        return "Database connection timed out: verify network access and database availability"

    if "ssl" in message or "tls" in message:
        return (
            "Database SSL configuration failed: verify SSL parameters in DATABASE_URL"
        )

    return "Database connection failed"


@lru_cache
def get_engine():
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        hide_parameters=True,  # never log bound params (may contain sensitive data)
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def check_database_connection() -> tuple[bool, str]:
    """Probe the database. Returns (True, ok_msg) or (False, generic_error_msg).

    Error message intentionally does NOT include the DSN or exception details
    to avoid leaking credentials or topology information in API responses.
    """
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection ok"
    except RuntimeError:
        # Missing env var — surface a safe, actionable message
        return (
            False,
            "Database is not configured: required environment variables are missing",
        )
    except SQLAlchemyError as error:
        safe_detail = _classify_database_error(error)
        logger.warning(
            "database_health_check_failed",
            extra={
                "error_type": error.__class__.__name__,
                "detail": safe_detail,
            },
        )
        return False, safe_detail
