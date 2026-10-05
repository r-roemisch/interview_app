"""Interview flow: start, answer, end. Every LLM failure leaves the database unchanged."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from interview_app.llm import LLMClient, LLMUnavailable, strip_code_fence
from interview_app.models import (
    OFF_TOPIC_LIMIT,
    QUESTION_CAP,
    Demeanor,
    Difficulty,
    Interview,
    InterviewStatus,
    Judge,
    Message,
    DEFAULT_INTERVIEWER_MODEL,
    MessageRole,
    Portrait,
    PromptStyle,
    Seniority,
)
from interview_app.prompts.interviewer import (
    FALLBACK_CLOSING,
    MAX_PLAN_CHARS,
    fallback_question,
    messages_for_closing,
    messages_for_next_question,
    messages_for_plan,
    reply_problem,
    split_reply,
)
from interview_app.prompts.persona import DEFAULT_PERSONA, Persona, messages_for_persona, persona_schema
from interview_app.services.off_topic import OffTopicCheck

log = logging.getLogger(__name__)


class InterviewStateError(Exception):
    """The requested action is not allowed in the Interview's current status."""


# Called after a Closing is persisted; the router uses it to schedule the Judge.
JudgeTrigger = Callable[[int], None]

# Strike 3 of the off-topic guard: a fixed Closing, no interviewer call (spec: interviewer-experiments).
OFF_TOPIC_CLOSING = "We'll stop the interview here, as the last answers were not about the interview."


def _append(interview: Interview, role: MessageRole, text: str, notes: str | None = None) -> Message:
    msg = Message(role=role, text=text, position=len(interview.messages), notes=notes)
    interview.messages.append(msg)
    return msg


def _interviewer_says(
    llm: LLMClient, interview: Interview, messages: list, *, closing: bool
) -> tuple[str, str | None]:
    """The interviewer's message and its Interviewer's Notes, checked: one more try when it fails,
    then a fixed fallback without notes (spec: security-guards B1, interviewer-experiments)."""
    for attempt in (1, 2):
        raw = llm.complete(messages, model=interview.interviewer_model)
        reply, notes = split_reply(interview.prompt_style, raw)
        problem = reply_problem(reply)
        if problem is None:
            return reply, notes
        log.warning("Interviewer reply rejected for interview %s (attempt %d): %s", interview.id, attempt, problem)
    log.warning("Interviewer fallback used for interview %s", interview.id)
    return (FALLBACK_CLOSING if closing else fallback_question(interview)), None


def create_plan(llm: LLMClient, interview: Interview) -> str | None:
    """Plan-ahead: one call with the Interviewer Model. A failure starts the Interview without a plan."""
    try:
        plan = llm.complete(messages_for_plan(interview), model=interview.interviewer_model).strip()
    except LLMUnavailable as exc:
        log.warning("Plan call failed, starting without a plan: %s", exc)
        return None
    return plan[:MAX_PLAN_CHARS] or None


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
    interviewer_model: str = DEFAULT_INTERVIEWER_MODEL,
    prompt_style: PromptStyle = PromptStyle.ZERO_SHOT,
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
        interviewer_model=interviewer_model,
        prompt_style=prompt_style,
        voice_interview=voice_interview,
        portrait=Portrait() if portrait else None,
    )
    persona = create_persona(llm, interview)
    interview.persona_name, interview.persona_title, interview.persona_voice = persona.name, persona.title, persona.voice
    if prompt_style == PromptStyle.PLAN_AHEAD:
        interview.plan = create_plan(llm, interview)
    first_question, notes = _interviewer_says(llm, interview, messages_for_next_question(interview), closing=False)
    _append(interview, MessageRole.QUESTION, first_question, notes)
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
    off_topic: OffTopicCheck | None = None,
) -> Interview:
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise InterviewStateError("Interview no longer accepts answers")
    if not interview.messages or interview.messages[-1].role != MessageRole.QUESTION:
        raise InterviewStateError("There is no open question to answer")

    if text.strip() and off_topic and off_topic(interview.messages[-1].text, text):
        return _off_topic_answer(db, interview, on_closing)
    _append(interview, MessageRole.ANSWER, text.strip())
    try:
        if interview.question_count < QUESTION_CAP:
            reply, notes = _interviewer_says(llm, interview, messages_for_next_question(interview), closing=False)
            _append(interview, MessageRole.QUESTION, reply, notes)
        else:
            closing_messages = messages_for_closing(interview, ended_early=False)
            reply, notes = _interviewer_says(llm, interview, closing_messages, closing=True)
            _append(interview, MessageRole.CLOSING, reply, notes)
            interview.status = InterviewStatus.JUDGING
    except Exception:
        db.rollback()
        raise
    db.commit()
    db.refresh(interview)
    if interview.status == InterviewStatus.JUDGING and on_closing:
        on_closing(interview.id)
    return interview


def _off_topic_answer(db: Session, interview: Interview, on_closing: JudgeTrigger | None) -> Interview:
    """The Answer is not kept and the interviewer is not called; the third one ends the Interview."""
    interview.off_topic_count += 1
    log.warning("Off-topic answer %d in interview %s", interview.off_topic_count, interview.id)
    ended = interview.off_topic_count >= OFF_TOPIC_LIMIT
    if ended:
        _append(interview, MessageRole.CLOSING, OFF_TOPIC_CLOSING)
        interview.ended_early = True
        # Without a real Answer the Judge has nothing to score.
        interview.status = InterviewStatus.JUDGING if interview.answer_count else InterviewStatus.EVALUATION_MISSING
    db.commit()
    db.refresh(interview)
    if ended and interview.status == InterviewStatus.JUDGING and on_closing:
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

    reply, notes = _interviewer_says(llm, interview, messages_for_closing(interview, ended_early=True), closing=True)
    _append(interview, MessageRole.CLOSING, reply, notes)
    interview.ended_early = True
    interview.status = InterviewStatus.JUDGING
    db.commit()
    db.refresh(interview)
    if on_closing:
        on_closing(interview.id)
    return interview
