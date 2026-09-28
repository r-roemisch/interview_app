"""SQLAlchemy tables. Vocabulary follows CONTEXT.md."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_app.db import Base

QUESTION_CAP = 10

# Fallback Persona when the Persona call fails (spec: Persona).
DEFAULT_PERSONA_NAME = "Alex Morgan"
DEFAULT_PERSONA_TITLE = "Hiring Manager"


class Seniority(StrEnum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


class Difficulty(StrEnum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"


class InterviewStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    JUDGING = "judging"
    COMPLETED = "completed"
    EVALUATION_MISSING = "evaluation_missing"


class MessageRole(StrEnum):
    QUESTION = "question"
    ANSWER = "answer"
    CLOSING = "closing"


class Verdict(StrEnum):
    STRONG_HIRE = "strong_hire"
    HIRE = "hire"
    NO_HIRE = "no_hire"


def _now() -> datetime:
    return datetime.now(UTC)


def _enum(enum_cls: type[StrEnum]) -> Enum:
    """Store the enum's value as a plain string; load it back as the enum."""
    return Enum(enum_cls, native_enum=False, length=32, values_callable=lambda e: [m.value for m in e])


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Job snapshot: copied into each Interview, never shared (spec: Reusing a Job).
    title: Mapped[str] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    seniority: Mapped[Seniority] = mapped_column(_enum(Seniority), default=Seniority.MID)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    difficulty: Mapped[Difficulty] = mapped_column(_enum(Difficulty), default=Difficulty.NORMAL)
    # Persona: invented per Interview, never copied by Practice again.
    persona_name: Mapped[str] = mapped_column(String(100), default=DEFAULT_PERSONA_NAME)
    persona_title: Mapped[str] = mapped_column(String(200), default=DEFAULT_PERSONA_TITLE)
    status: Mapped[InterviewStatus] = mapped_column(_enum(InterviewStatus), default=InterviewStatus.IN_PROGRESS)
    ended_early: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    messages: Mapped[list[Message]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        order_by="Message.position",
    )
    evaluation: Mapped[Evaluation | None] = relationship(
        back_populates="interview", cascade="all, delete-orphan", uselist=False
    )

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

    id: Mapped[int] = mapped_column(primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id", ondelete="CASCADE"), unique=True, index=True
    )
    overall_score: Mapped[int] = mapped_column(Integer)
    justification: Mapped[str] = mapped_column(Text)
    verdict: Mapped[Verdict] = mapped_column(_enum(Verdict))
    # list[str], exactly three
    improvement_points: Mapped[list] = mapped_column(JSON)
    # list[dict] in Answer order, shape = schemas.StarBreakdown
    star_breakdowns: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    interview: Mapped[Interview] = relationship(back_populates="evaluation")
