import os
from collections.abc import Iterator

# Safety net, set before the app is imported: a model client a test forgets to replace with a fake
# becomes an offline dev fake instead of a real, paid call with the key from .env.
os.environ["LLM_PROVIDER"] = "fake"

import pytest
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from interview_app import db as db_module
from interview_app.budget import FakeDailySpend, get_daily_spend
from interview_app.db import Base, get_db, get_session_factory
from interview_app.images import FakeImageClient, get_image_client
from interview_app.jev import FakeJevClient, get_jev_client
from interview_app.llm import FakeLLMClient, get_llm_client
from interview_app.main import create_app
from interview_app.services.off_topic import FakeOffTopicCheck, get_off_topic_check
from interview_app.speech import FakeSpeechClient, get_speech_client


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
def llm() -> FakeLLMClient:
    """Scripted LLM. Tests append to `llm.responses` before making requests."""
    return FakeLLMClient()


@pytest.fixture
def jev() -> FakeJevClient:
    """Scripted JEV. Tests append answer dicts to `jev.responses`."""
    return FakeJevClient()


@pytest.fixture
def speech() -> FakeSpeechClient:
    """Fixed speech and transcription. Set `speech.error` to make every call fail."""
    return FakeSpeechClient()


@pytest.fixture
def images() -> FakeImageClient:
    """A fixed Portrait. Put exceptions in `images.errors` to make the next calls fail."""
    return FakeImageClient()


@pytest.fixture
def off_topic() -> FakeOffTopicCheck:
    """Every Answer is on-topic unless a test adds it to `off_topic.off_topic`."""
    return FakeOffTopicCheck()


@pytest.fixture
def daily_spend() -> FakeDailySpend:
    """Today's spending; None (unknown) unless a test sets `daily_spend.value`."""
    return FakeDailySpend()


@pytest.fixture
def client(engine, db, llm, jev, speech, images, off_topic, daily_spend, monkeypatch) -> Iterator[TestClient]:
    """TestClient wired to the in-memory database and the fake LLM."""
    monkeypatch.setattr(db_module, "engine", engine)
    app = create_app()

    def override_get_db():
        yield db

    def override_llm():
        yield llm

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_client] = override_llm
    app.dependency_overrides[get_jev_client] = lambda: jev
    app.dependency_overrides[get_speech_client] = lambda: speech
    app.dependency_overrides[get_image_client] = lambda: images
    app.dependency_overrides[get_off_topic_check] = lambda: off_topic
    app.dependency_overrides[get_daily_spend] = daily_spend
    app.dependency_overrides[get_session_factory] = lambda: sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    with TestClient(app) as c:
        yield c

