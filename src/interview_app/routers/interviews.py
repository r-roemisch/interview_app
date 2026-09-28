from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from interview_app.db import get_db, get_session_factory
from interview_app.jev import JevClient, get_jev_client
from interview_app.llm import LLMClient, LLMUnavailable, get_llm_client
from interview_app.models import Difficulty, Interview, InterviewStatus, Judge, Seniority
from interview_app.schemas import EvaluationOut, HistoryRow, InterviewOut
from interview_app.services import interview as svc
from interview_app.services import judge

router = APIRouter(prefix="/interviews", tags=["interviews"])


class InterviewCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=200)
    seniority: Seniority = Seniority.MID
    job_description: str | None = None
    difficulty: Difficulty = Difficulty.NORMAL
    cv: str | None = Field(default=None, max_length=20_000)
    judge: Judge = Judge.LLM
    voice_interview: bool = False


class AnswerIn(BaseModel):
    text: str = Field(default="", max_length=10_000)


def load_interview(interview_id: int, db: Session = Depends(get_db)) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    return interview


def _llm_unavailable(exc: LLMUnavailable) -> HTTPException:
    return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"The interviewer is unavailable: {exc}")


def _judge_trigger(background: BackgroundTasks, session_factory, llm: LLMClient, jev: JevClient):
    """Schedule the chosen Judge for an Interview once its Closing is stored (ADR-0002, ADR-0003)."""

    def trigger(interview_id: int) -> None:
        background.add_task(
            judge.run_judge_in_background, interview_id, session_factory=session_factory, llm=llm, jev=jev
        )

    return trigger


@router.post("", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def create_interview(
    body: InterviewCreate,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> Interview:
    try:
        return svc.start_interview(
            db,
            llm,
            title=body.title,
            industry=body.industry,
            seniority=body.seniority,
            job_description=body.job_description,
            difficulty=body.difficulty,
            cv=body.cv,
            judge=body.judge,
            voice_interview=body.voice_interview,
        )
    except LLMUnavailable as exc:
        raise _llm_unavailable(exc) from exc


@router.get("", response_model=list[HistoryRow])
def list_interviews(db: Session = Depends(get_db)) -> list[HistoryRow]:
    rows = db.scalars(select(Interview).order_by(Interview.created_at.desc(), Interview.id.desc())).all()
    return [
        HistoryRow(
            id=i.id,
            title=i.title,
            created_at=i.created_at,
            status=i.status,
            judge=i.judge,
            overall_score=i.evaluation.overall_score if i.evaluation else None,
        )
        for i in rows
    ]


@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview: Interview = Depends(load_interview)) -> Interview:
    return interview


@router.post("/{interview_id}/answers", response_model=InterviewOut)
def submit_answer(
    body: AnswerIn,
    background: BackgroundTasks,
    interview: Interview = Depends(load_interview),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    session_factory=Depends(get_session_factory),
    jev: JevClient = Depends(get_jev_client),
) -> Interview:
    trigger = _judge_trigger(background, session_factory, llm, jev)
    try:
        return svc.submit_answer(db, llm, interview, body.text, on_closing=trigger)
    except svc.InterviewStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except LLMUnavailable as exc:
        raise _llm_unavailable(exc) from exc


@router.post("/{interview_id}/end", response_model=InterviewOut)
def end_interview(
    background: BackgroundTasks,
    interview: Interview = Depends(load_interview),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    session_factory=Depends(get_session_factory),
    jev: JevClient = Depends(get_jev_client),
) -> Interview:
    trigger = _judge_trigger(background, session_factory, llm, jev)
    try:
        return svc.end_interview(db, llm, interview, on_closing=trigger)
    except svc.InterviewStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except LLMUnavailable as exc:
        raise _llm_unavailable(exc) from exc


@router.get("/{interview_id}/evaluation", response_model=EvaluationOut)
def get_evaluation(interview: Interview = Depends(load_interview)):
    if interview.status == InterviewStatus.EVALUATION_MISSING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Evaluation could not be produced; re-run the judge")
    if interview.evaluation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evaluation not ready")
    return interview.evaluation


@router.get("/{interview_id}/evaluations", response_model=list[EvaluationOut])
def list_evaluations(interview: Interview = Depends(load_interview)):
    """Every Evaluation of the Interview (at most one per Judge), for the comparison."""
    return interview.evaluations


@router.post(
    "/{interview_id}/evaluations/{judge_name}",
    response_model=EvaluationOut,
    status_code=status.HTTP_201_CREATED,
)
def run_other_judge(
    judge_name: Judge,
    interview: Interview = Depends(load_interview),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    jev: JevClient = Depends(get_jev_client),
):
    """Run the Judge that was not chosen, synchronously. Its failure never changes the status."""
    if interview.status == InterviewStatus.IN_PROGRESS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview has not ended")
    if judge_name == interview.judge:
        raise HTTPException(status.HTTP_409_CONFLICT, "This is the chosen Judge; use Re-run evaluation")
    evaluation = judge.run_other_judge(db, llm, jev, interview, judge_name)
    if evaluation is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, f"The {judge_name.value.upper()} Judge could not produce an Evaluation; try again"
        )
    return evaluation


@router.post(
    "/{interview_id}/evaluation/rerun",
    response_model=InterviewOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def rerun_evaluation(
    background: BackgroundTasks,
    interview: Interview = Depends(load_interview),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    session_factory=Depends(get_session_factory),
    jev: JevClient = Depends(get_jev_client),
) -> Interview:
    if interview.status not in (InterviewStatus.COMPLETED, InterviewStatus.EVALUATION_MISSING):
        raise HTTPException(status.HTTP_409_CONFLICT, "Interview has not ended")
    judge.replace_evaluation(db, interview, interview.judge, None)
    interview.status = InterviewStatus.JUDGING
    db.commit()
    db.refresh(interview)
    _judge_trigger(background, session_factory, llm, jev)(interview.id)
    return interview


@router.delete("/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview(interview: Interview = Depends(load_interview), db: Session = Depends(get_db)) -> Response:
    db.delete(interview)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{interview_id}/practice-again", response_model=InterviewOut, status_code=status.HTTP_201_CREATED)
def practice_again(
    interview: Interview = Depends(load_interview),
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> Interview:
    """New Interview from the same Job snapshot, Difficulty, CV, Judge and voice setting; fresh Persona."""
    try:
        return svc.start_interview(
            db,
            llm,
            title=interview.title,
            industry=interview.industry,
            seniority=interview.seniority,
            job_description=interview.job_description,
            difficulty=interview.difficulty,
            cv=interview.cv,
            judge=interview.judge,
            voice_interview=interview.voice_interview,
        )
    except LLMUnavailable as exc:
        raise _llm_unavailable(exc) from exc
