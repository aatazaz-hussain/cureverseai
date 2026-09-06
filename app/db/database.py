import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BASE_DIR = Path(__file__).resolve().parents[2]


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    """
    Return the PostgreSQL connection URL.

    Environment variable:
        CUREVERSEAI_DATABASE_URL

    Example:
        postgresql+psycopg://user:password@localhost:5432/cureverseai
    """

    database_url = os.getenv("CUREVERSEAI_DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "CUREVERSEAI_DATABASE_URL is not set. "
            "Set it before starting the CureVerseAI backend."
        )

    return database_url


def create_database_engine():
    """
    Create the SQLAlchemy engine for CureVerseAI PostgreSQL.
    """

    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )


engine = create_database_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    """
    Provide a database session for application services/API routes.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def test_database_connection() -> dict:
    """
    Verify that CureVerseAI can communicate with PostgreSQL.
    """

    with engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    current_database(),
                    current_user,
                    version()
                """
            )
        )

        row = result.fetchone()

    return {
        "database": row[0],
        "user": row[1],
        "postgresql_version": row[2],
    }
