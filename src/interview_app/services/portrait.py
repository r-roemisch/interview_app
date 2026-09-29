"""Portrait generation: in the background after the Interview starts, never blocking it (spec: portrait)."""

from __future__ import annotations

import logging
from collections.abc import Callable

from sqlalchemy import update
from sqlalchemy.orm import Session

from interview_app import db as db_module
from interview_app.images import ImageClient, _default_image_client
from interview_app.llm import LLMUnavailable
from interview_app.models import Interview, Portrait, PortraitStatus
from interview_app.prompts.portrait import portrait_prompt

log = logging.getLogger(__name__)


def generate_in_background(
    interview_id: int,
    *,
    session_factory: Callable[[], Session] | None = None,
    images: ImageClient | None = None,
) -> None:
    """Entry point for FastAPI BackgroundTasks: Ready on success, Failed after two failed tries."""
    db = (session_factory or db_module.SessionLocal)()
    client = images or _default_image_client()
    try:
        interview = db.get(Interview, interview_id)
        if interview is None or interview.portrait is None:
            return
        prompt = portrait_prompt(interview)
        image = None
        for attempt in (1, 2):
            try:
                image = client.portrait(prompt)
                break
            except LLMUnavailable as exc:
                log.warning("Portrait for interview %s failed (attempt %d): %s", interview_id, attempt, exc)
        interview.portrait.image = image
        interview.portrait.status = PortraitStatus.READY if image else PortraitStatus.FAILED
        db.commit()
    except Exception:
        # e.g. the Interview was deleted while its Portrait was being made
        log.exception("Portrait crashed for interview %s", interview_id)
        db.rollback()
    finally:
        db.close()


def fail_unfinished_portraits(db: Session) -> None:
    """Called at startup: a restart loses the background task, so a Pending Portrait would never finish."""
    db.execute(
        update(Portrait).where(Portrait.status == PortraitStatus.PENDING).values(status=PortraitStatus.FAILED)
    )
    db.commit()
