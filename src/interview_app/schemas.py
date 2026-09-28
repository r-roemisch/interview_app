"""Pydantic models for the JSON API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from interview_app.models import Difficulty, InterviewStatus, Judge, MessageRole, Seniority, Verdict


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    text: str
    position: int


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    industry: str | None
    seniority: Seniority
    job_description: str | None
    difficulty: Difficulty
    judge: Judge
    persona_name: str
    persona_title: str
    persona_voice: str
    voice_interview: bool
    status: InterviewStatus
    ended_early: bool
    created_at: datetime
    question_count: int
    question_cap: int = 10
    messages: list[MessageOut]


class HistoryRow(BaseModel):
    id: int
    title: str
    created_at: datetime
    status: InterviewStatus
    judge: Judge
    overall_score: int | None


class StarRating(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None  # None from the JEV Judge
    confidence: float | None = None  # JEV Judge only


class ChecklistResult(BaseModel):
    check: str
    probability: float  # JEV's probability that the check is met


class StarBreakdown(BaseModel):
    """Assessment of one Answer. `position` is the Answer's message position."""

    position: int
    situation: StarRating
    task: StarRating
    action: StarRating
    result: StarRating


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    interview_id: int
    judge: Judge
    overall_score: int = Field(ge=0, le=100)
    justification: str | None
    verdict: Verdict
    improvement_points: list[str]
    star_breakdowns: list[StarBreakdown]
    overall_confidence: float | None
    verdict_confidence: float | None
    checklist: list[ChecklistResult] | None
    created_at: datetime
