"""Interview flow: start, answer, end. Every LLM failure leaves the database unchanged."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from interview_app.llm import LLMClient, LLMUnavailable, strip_code_fence
from interview_app.models import (
    QUESTION_CAP,
    Difficulty,
    Interview,
    InterviewStatus,
    Message,
    MessageRole,
    Seniority,
)
from interview_app.prompts.interviewer import messages_for_closing, messages_for_next_question
from interview_app.prompts.persona import DEFAULT_PERSONA, Persona, messages_for_persona, persona_schema

log = logging.getLogger(__name__)


class InterviewStateError(Exception):
    """The requested action is not allowed in the Interview's current status."""


# Called after a Closing is persisted. Issue 05 registers the Judge here.
JudgeTrigger = Callable[[int], None]


def _append(interview: Interview, role: MessageRole, text: str) -> Message:
    msg = Message(role=role, text=text, position=len(interview.messages))
    interview.messages.append(msg)
    return msg


def create_persona(llm: LLMClient, interview: Interview) -> Persona:
    """One call, no retry on bad output. Any failure falls back to DEFAULT_PERSONA (spec: Persona)."""
    try:
        raw = llm.complete(messages_for_persona(interview), json_schema=persona_schema())
        return Persona.model_validate(json.loads(strip_code_fence(raw)))
    except (LLMUnavailable, json.JSONDecodeError, ValidationError) as exc:
        log.warning("Persona call failed, using the default Persona: %s", exc)
        return DEFAULT_PERSONA


def start_interview(
    db: Session,
    llm: LLMClient,
    *,
    title: str,
    industry: str | None,
    seniority: Seniority,
    job_description: str | None,
    difficulty: Difficulty,
) -> Interview:
    interview = Interview(
        title=title.strip(),
        industry=industry.strip() if industry else None,
        seniority=seniority,
        job_description=job_description.strip() if job_description else None,
        difficulty=difficulty,
    )
    persona = create_persona(llm, interview)
    interview.persona_name, interview.persona_title = persona.name, persona.title
    first_question = llm.complete(messages_for_next_question(interview))
    _append(interview, MessageRole.QUESTION, first_question.strip())
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview


def submit_answer(
    db: Session,
    llm: LLMClient,
    interview: Interview,
    text: str,
    *,
    on_closing: JudgeTrigger | None = None,
) -> Interview:
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise InterviewStateError("Interview no longer accepts answers")
    if not interview.messages or interview.messages[-1].role != MessageRole.QUESTION:
        raise InterviewStateError("There is no open question to answer")

    _append(interview, MessageRole.ANSWER, text.strip())
    try:
        if interview.question_count < QUESTION_CAP:
            reply = llm.complete(messages_for_next_question(interview))
            _append(interview, MessageRole.QUESTION, reply.strip())
        else:
            reply = llm.complete(messages_for_closing(interview, ended_early=False))
            _append(interview, MessageRole.CLOSING, reply.strip())
            interview.status = InterviewStatus.JUDGING
    except Exception:
        db.rollback()
        raise
    db.commit()
    db.refresh(interview)
    if interview.status == InterviewStatus.JUDGING and on_closing:
        on_closing(interview.id)
    return interview


def end_interview(
    db: Session,
    llm: LLMClient,
    interview: Interview,
    *,
    on_closing: JudgeTrigger | None = None,
) -> Interview:
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise InterviewStateError("Interview is not in progress")
    if interview.answer_count == 0:
        raise InterviewStateError("Answer at least one question before ending the interview")

    reply = llm.complete(messages_for_closing(interview, ended_early=True))
    _append(interview, MessageRole.CLOSING, reply.strip())
    interview.ended_early = True
    interview.status = InterviewStatus.JUDGING
    db.commit()
    db.refresh(interview)
    if on_closing:
        on_closing(interview.id)
    return interview
