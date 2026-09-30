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
    Demeanor,
    Difficulty,
    Interview,
    InterviewStatus,
    Judge,
    Message,
    MessageRole,
    Portrait,
    Seniority,
)
from interview_app.prompts.interviewer import (
    FALLBACK_CLOSING,
    fallback_question,
    messages_for_closing,
    messages_for_next_question,
    reply_problem,
)
from interview_app.prompts.persona import DEFAULT_PERSONA, Persona, messages_for_persona, persona_schema

log = logging.getLogger(__name__)


class InterviewStateError(Exception):
    """The requested action is not allowed in the Interview's current status."""


# Called after a Closing is persisted; the router uses it to schedule the Judge.
JudgeTrigger = Callable[[int], None]


def _append(interview: Interview, role: MessageRole, text: str) -> Message:
    msg = Message(role=role, text=text, position=len(interview.messages))
    interview.messages.append(msg)
    return msg


def _interviewer_says(llm: LLMClient, interview: Interview, messages: list, *, closing: bool) -> str:
    """The interviewer's reply, checked: one more try when it fails, then a fixed fallback (spec: B1)."""
    for attempt in (1, 2):
        reply = llm.complete(messages).strip()
        problem = reply_problem(reply)
        if problem is None:
            return reply
        log.warning("Interviewer reply rejected for interview %s (attempt %d): %s", interview.id, attempt, problem)
    log.warning("Interviewer fallback used for interview %s", interview.id)
    return FALLBACK_CLOSING if closing else fallback_question(interview)


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
    demeanor: Demeanor = Demeanor.FRIENDLY,
    cv: str | None = None,
    judge: Judge = Judge.LLM,
    voice_interview: bool = False,
    portrait: bool = False,
) -> Interview:
    """Commits the Interview with its first Question. With `portrait`, a Pending Portrait is added;
    the caller schedules its generation."""
    interview = Interview(
        title=title.strip(),
        industry=industry.strip() if industry else None,
        seniority=seniority,
        job_description=job_description.strip() if job_description else None,
        difficulty=difficulty,
        demeanor=demeanor,
        cv=(cv or "").strip() or None,
        judge=judge,
        voice_interview=voice_interview,
        portrait=Portrait() if portrait else None,
    )
    persona = create_persona(llm, interview)
    interview.persona_name, interview.persona_title, interview.persona_voice = persona.name, persona.title, persona.voice
    first_question = _interviewer_says(llm, interview, messages_for_next_question(interview), closing=False)
    _append(interview, MessageRole.QUESTION, first_question)
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
            reply = _interviewer_says(llm, interview, messages_for_next_question(interview), closing=False)
            _append(interview, MessageRole.QUESTION, reply)
        else:
            reply = _interviewer_says(llm, interview, messages_for_closing(interview, ended_early=False), closing=True)
            _append(interview, MessageRole.CLOSING, reply)
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

    reply = _interviewer_says(llm, interview, messages_for_closing(interview, ended_early=True), closing=True)
    _append(interview, MessageRole.CLOSING, reply)
    interview.ended_early = True
    interview.status = InterviewStatus.JUDGING
    db.commit()
    db.refresh(interview)
    if on_closing:
        on_closing(interview.id)
    return interview
