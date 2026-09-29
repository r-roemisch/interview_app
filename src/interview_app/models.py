"""SQLAlchemy tables. Vocabulary follows CONTEXT.md."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_app.db import Base

QUESTION_CAP = 10

# Fallback Persona when the Persona call fails (spec: Persona).
DEFAULT_PERSONA_NAME = "Alex Morgan"
DEFAULT_PERSONA_TITLE = "Hiring Manager"

# The voices a Persona can speak with in a Voice Interview (OpenAI voices of TTS_MODEL),
# each with a description so the Persona call can pick one that fits the name (spec: voice-interview).
PERSONA_VOICES = {
    "marin": "clear, female-sounding",
    "coral": "warm, female-sounding",
    "sage": "calm, female-sounding",
    "cedar": "clear, male-sounding",
    "ash": "firm, male-sounding",
    "echo": "calm, male-sounding",
}
DEFAULT_PERSONA_VOICE = "cedar"


class Seniority(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class Difficulty(StrEnum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class Judge(StrEnum):
    LLM = "llm"
    JEV = "jev"


class InterviewStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    JUDGING = "judging"
    COMPLETED = "completed"
    EVALUATION_MISSING = "evaluation_missing"


class MessageRole(StrEnum):
    QUESTION = "question"
    ANSWER = "answer"
    CLOSING = "closing"


class PortraitStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


class Verdict(StrEnum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    NO_HIRE = "no_hire"


def _now() -> datetime:
    return datetime.now(UTC)


def _enum(enum_cls: type[StrEnum]) -> Enum:
    """Store the enum's value as a plain string; load it back as the enum."""
    return Enum(enum_cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


class UTCDateTime(TypeDecorator):
    """SQLite drops the time zone on save. Every stored time is UTC, so put it back on load;
    otherwise the API sends times without an offset and browsers read them as local time."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Job snapshot: copied into each Interview, never shared (spec: Reusing a Job).
    title: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seniority: Mapped[Seniority] = mapped_column(_enum(Seniority), default=Seniority.MID)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # CV: a snapshot per Interview like the Job, read only by the interviewer (CONTEXT.md).
    cv: Mapped[str | None] = mapped_column(Text, nullable=True)

    difficulty: Mapped[Difficulty] = mapped_column(_enum(Difficulty), default=Difficulty.NORMAL)
    # The chosen Judge: its Evaluation decides the status and the History score (ADR-0003).
    judge: Mapped[Judge] = mapped_column(_enum(Judge), default=Judge.LLM)
    # Persona: invented per Interview, never copied by Practice again.
    persona_name: Mapped[str] = mapped_column(String(100), default=DEFAULT_PERSONA_NAME)
    persona_title: Mapped[str] = mapped_column(String(200), default=DEFAULT_PERSONA_TITLE)
    persona_voice: Mapped[str] = mapped_column(String(32), default=DEFAULT_PERSONA_VOICE)
    # Voice Interview: Questions and the Closing are spoken, Answers can be spoken (CONTEXT.md).
    voice_interview: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[InterviewStatus] = mapped_column(_enum(InterviewStatus), default=InterviewStatus.IN_PROGRESS)
    ended_early: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_now)

    messages: Mapped[list[Message]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="Message.position",
    )
    # At most one Evaluation per Judge.
    evaluations: Mapped[list[Evaluation]] = relationship(back_populates="interview", cascade="all, delete-orphan")
    # None when no Portrait was asked for at Setup (and for Interviews from before Portraits).
    portrait: Mapped[Portrait | None] = relationship(back_populates="interview", cascade="all, delete-orphan")

    @property
    def portrait_state(self) -> str:
        return self.portrait.status.value if self.portrait else "none"

    @property
    def evaluation(self) -> Evaluation | None:
        """The chosen Judge's Evaluation."""
        return self.evaluation_by(self.judge)

    def evaluation_by(self, judge: Judge) -> Evaluation | None:
        return next((e for e in self.evaluations if e.judge == judge), None)

    @property
    def question_count(self) -> int:
        return sum(1 for m in self.messages if m.role == MessageRole.QUESTION)

    @property
    def answer_count(self) -> int:
        return sum(1 for m in self.messages if m.role == MessageRole.ANSWER)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("interview_id", "position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    role: Mapped[MessageRole] = mapped_column(_enum(MessageRole))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)

    interview: Mapped[Interview] = relationship(back_populates="messages")


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (UniqueConstraint("interview_id", "judge"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    judge: Mapped[Judge] = mapped_column(_enum(Judge), default=Judge.LLM)
    overall_score: Mapped[int] = mapped_column(Integer)
    # The JEV Judge writes no text: no justification, no STAR comments (ADR-0003).
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    verdict: Mapped[Verdict] = mapped_column(_enum(Verdict))
    # JEV's confidence (0-1) in the Overall Score and the Verdict; None for the LLM Judge.
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    # JEV only: list[{"check": str, "probability": float}], the Checklist in order.
    checklist: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # list[str], exactly three
    improvement_points: Mapped[list] = mapped_column(JSON)
    # list[dict] in Answer order, shape = schemas.StarBreakdown (comment None and confidence set for JEV)
    star_breakdowns: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_now)

    interview: Mapped[Interview] = relationship(back_populates="evaluations")


class Portrait(Base):
    """The Persona's Portrait (CONTEXT.md). Its own table, so adding it needed no change to `interviews`."""

    __tablename__ = "portraits"

    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), primary_key=True)
    status: Mapped[PortraitStatus] = mapped_column(_enum(PortraitStatus), default=PortraitStatus.PENDING)
    # The PNG as generated (about 1.3 MB), None until ready. Deferred: loaded only when served.
    image: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True, deferred=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_now)

    interview: Mapped[Interview] = relationship(back_populates="portrait")
