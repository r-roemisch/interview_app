"""Pydantic models for the JSON API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from interview_app.models import Difficulty, InterviewStatus, MessageRole, Seniority, Verdict


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
    overall_score: int | None


class StarRating(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str


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
    overall_score: int = Field(ge=0, le=100)
    justification: str
    verdict: Verdict
    improvement_points: list[str]
    star_breakdowns: list[StarBreakdown]
    created_at: datetime
