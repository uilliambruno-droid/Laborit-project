import os
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


def get_database_url() -> str:
    explicit_database_url = os.getenv("DATABASE_URL")
    if explicit_database_url:
        return explicit_database_url

    db_user = os.getenv("DB_USER", "user_read_only")
    db_password = os.getenv("DB_PASSWORD", "laborit_teste_2789")
    db_host = os.getenv("DB_HOST", "northwind-mysql-db.ccghzwgwh2c7.us-east-1.rds.amazonaws.com")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "northwind")
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


@lru_cache
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)


def check_database_connection() -> tuple[bool, str]:
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database connection ok"
    except SQLAlchemyError as error:
        return False, f"Database connection failed: {error.__class__.__name__}"
