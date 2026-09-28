"""Judge: turns a finished transcript into an Evaluation. Runs in the background after the Closing.

Two Judges (ADR-0003): the LLM Judge here, the JEV Judge in `jev_judge`.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from pydantic import ValidationError
from sqlalchemy.orm import Session

from interview_app import db as db_module
from interview_app.jev import JevClient, _default_jev_client
from interview_app.llm import LLMClient, LLMUnavailable, _default_client, strip_code_fence
from interview_app.models import Evaluation, Interview, InterviewStatus, Judge, MessageRole
from interview_app.prompts.judge import JudgeOutput, judge_json_schema, messages_for_judge
from interview_app.services import jev_judge

log = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


class JudgeOutputInvalid(Exception):
    pass


def _parse(raw: str, expected_answers: int) -> JudgeOutput:
    try:
        data = json.loads(strip_code_fence(raw))
    except json.JSONDecodeError as exc:
        raise JudgeOutputInvalid(f"not valid JSON ({exc.msg})") from exc
    try:
        out = JudgeOutput.model_validate(data)
    except ValidationError as exc:
        raise JudgeOutputInvalid(str(exc)) from exc
    if len(out.answers) != expected_answers:
        raise JudgeOutputInvalid(
            f"`answers` has {len(out.answers)} entries, expected {expected_answers}"
        )
    return out


def _to_evaluation(interview: Interview, out: JudgeOutput) -> Evaluation:
    answer_positions = [m.position for m in interview.messages if m.role == MessageRole.ANSWER]
    breakdowns = [
        {"position": pos, **assessment.model_dump()}
        for pos, assessment in zip(answer_positions, out.answers, strict=True)
    ]
    return Evaluation(
        overall_score=out.overall_score,
        justification=out.justification.strip(),
        verdict=out.verdict,
        improvement_points=[p.strip() for p in out.improvement_points],
        star_breakdowns=breakdowns,
    )


def _llm_evaluation(llm: LLMClient, interview: Interview) -> Evaluation | None:
    """The LLM Judge: one retry on invalid output, none when the model is unavailable."""
    expected = interview.answer_count
    schema = judge_json_schema()
    previous_error: str | None = None
    for attempt in (1, 2):
        try:
            raw = llm.complete(messages_for_judge(interview, previous_error=previous_error), json_schema=schema)
            return _to_evaluation(interview, _parse(raw, expected))
        except JudgeOutputInvalid as exc:
            previous_error = str(exc)[:500]
            log.warning("Judge output invalid for interview %s (attempt %d): %s", interview.id, attempt, exc)
        except LLMUnavailable as exc:
            log.error("Judge LLM unavailable for interview %s: %s", interview.id, exc)
            return None
    return None


def evaluate(judge: Judge, interview: Interview, *, llm: LLMClient, jev: JevClient) -> Evaluation | None:
    if judge == Judge.JEV:
        return jev_judge.evaluate(jev, interview)
    return _llm_evaluation(llm, interview)


def replace_evaluation(db: Session, interview: Interview, judge: Judge, evaluation: Evaluation | None) -> None:
    """Swap one Judge's Evaluation. The old row is deleted and flushed first, so the
    (interview_id, judge) unique constraint never sees two rows."""
    old = interview.evaluation_by(judge)
    if old is not None:
        interview.evaluations.remove(old)
        db.flush()
    if evaluation is not None:
        evaluation.judge = judge
        interview.evaluations.append(evaluation)


def run_judge(db: Session, llm: LLMClient, interview: Interview, *, jev: JevClient | None = None) -> Interview:
    """Run the chosen Judge: Completed on success, Evaluation Missing on failure. Always commits."""
    if interview.status not in (
        InterviewStatus.JUDGING,
        InterviewStatus.COMPLETED,
        InterviewStatus.EVALUATION_MISSING,
    ):
        raise ValueError("Interview has not ended")

    evaluation = evaluate(interview.judge, interview, llm=llm, jev=jev or _default_jev_client())
    replace_evaluation(db, interview, interview.judge, evaluation)
    interview.status = InterviewStatus.COMPLETED if evaluation else InterviewStatus.EVALUATION_MISSING
    db.commit()
    db.refresh(interview)
    return interview


def run_other_judge(db: Session, llm: LLMClient, jev: JevClient, interview: Interview, judge: Judge) -> Evaluation | None:
    """Run the Judge that was not chosen, for the comparison. Replaces that Judge's earlier Evaluation
    on success; on failure nothing changes. Never touches the status (spec: Evaluation page)."""
    evaluation = evaluate(judge, interview, llm=llm, jev=jev)
    if evaluation is None:
        return None
    replace_evaluation(db, interview, judge, evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def run_judge_in_background(
    interview_id: int,
    *,
    session_factory: SessionFactory | None = None,
    llm: LLMClient | None = None,
    jev: JevClient | None = None,
) -> None:
    """Entry point for FastAPI BackgroundTasks. Uses its own session because the request's is closed."""
    factory = session_factory or db_module.SessionLocal
    client = llm or _default_client()
    db = factory()
    try:
        interview = db.get(Interview, interview_id)
        if interview is None:
            log.warning("Judge: interview %s vanished before judging", interview_id)
            return
        run_judge(db, client, interview, jev=jev)
    except Exception:
        log.exception("Judge crashed for interview %s", interview_id)
        db.rollback()
        interview = db.get(Interview, interview_id)
        if interview is not None and interview.status == InterviewStatus.JUDGING:
            interview.status = InterviewStatus.EVALUATION_MISSING
            db.commit()
    finally:
        db.close()
