from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from interview_app import db as db_module
from interview_app.db import Base, get_db
from interview_app.main import create_app


@pytest.fixture
def engine():
    """A fresh in-memory SQLite database per test."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    import interview_app.models  # noqa: F401

    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(engine, db, monkeypatch) -> Iterator[TestClient]:
    """TestClient wired to the in-memory database, with startup table creation pointed at it."""
    monkeypatch.setattr(db_module, "engine", engine)
    app = create_app()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

