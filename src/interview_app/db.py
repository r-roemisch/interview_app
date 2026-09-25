from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from interview_app.config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def create_tables() -> None:
    # Models must be imported so their tables are registered on Base.metadata.
    import interview_app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session_factory() -> sessionmaker:
    """FastAPI dependency for code that must open its own session (background tasks)."""
    return SessionLocal


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
