"""Judge prompt and output schema (ADR-0002)."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from interview_app.llm import Message
from interview_app.models import Interview, MessageRole, Verdict


class JudgeStarRating(BaseModel):
    rating: int = Field(ge=1, le=5, description="1 = absent or very weak, 5 = excellent")
    comment: str = Field(min_length=1, description="One sentence")


class JudgeAnswerAssessment(BaseModel):
    situation: JudgeStarRating
    task: JudgeStarRating
    action: JudgeStarRating
    result: JudgeStarRating


class JudgeOutput(BaseModel):
    """What the Judge must return. `answers` is in transcript order, one entry per Answer."""

    answers: list[JudgeAnswerAssessment]
    overall_score: int = Field(ge=0, le=100)
    justification: str = Field(min_length=1, description="One paragraph")
    verdict: Verdict
    improvement_points: list[str] = Field(min_length=3, max_length=3)

    @field_validator("verdict", mode="before")
    @classmethod
    def _normalize_verdict(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower().replace(" ", "_").replace("-", "_")
        return v


def judge_json_schema() -> dict[str, Any]:
    return JudgeOutput.model_json_schema()


def _job_block(interview: Interview) -> str:
    lines = [
        f"Title: {interview.title}",
        f"Seniority: {interview.seniority.value}",
        f"Industry: {interview.industry or 'not specified'}",
    ]
    if interview.job_description:
        lines += ["Job description:", interview.job_description.strip()]
    return "\n".join(lines)


def _transcript_block(interview: Interview) -> str:
    lines = []
    answer_no = 0
    for m in interview.messages:
        if m.role == MessageRole.QUESTION:
            lines.append(f"INTERVIEWER: {m.text}")
        elif m.role == MessageRole.ANSWER:
            answer_no += 1
            lines.append(f"CANDIDATE (answer {answer_no}): {m.text or '(no answer given)'}")
    return "\n\n".join(lines)


def messages_for_judge(interview: Interview, *, previous_error: str | None = None) -> list[Message]:
    answer_count = interview.answer_count
    system = "\n".join(
        [
            "You are an experienced hiring manager evaluating a behavioral interview transcript.",
            "You were not the interviewer. Judge only what the candidate said.",
            "For every candidate answer, rate each STAR component (Situation, Task, Action, Result)",
            "from 1 to 5 with a one-sentence comment. An empty or off-topic answer scores 1 on all four.",
            "Then give an overall score from 0 to 100 for the whole interview, judged on both STAR",
            "structure and fit for the position, with a one-paragraph justification.",
            "Give a verdict: strong_hire, hire, or no_hire.",
            "Give exactly three specific, actionable improvement points.",
            f"Return exactly {answer_count} entries in `answers`, in transcript order.",
            "Return ONLY a JSON object matching this schema, with no prose before or after it:",
            json.dumps(judge_json_schema()),
        ]
    )
    user = "\n\n".join(
        [
            "POSITION\n" + _job_block(interview),
            "TRANSCRIPT\n" + _transcript_block(interview),
            f"Now evaluate. `answers` must have {answer_count} entries.",
        ]
    )
    msgs: list[Message] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    if previous_error:
        msgs.append(
            {
                "role": "system",
                "content": (
                    "Your previous output was rejected: "
                    f"{previous_error}\nReturn only a valid JSON object matching the schema."
                ),
            }
        )
    return msgs
