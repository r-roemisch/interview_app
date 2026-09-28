from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from interview_app.db import get_db
from interview_app.models import Interview

router = APIRouter(prefix="/cv", tags=["setup"])


class LatestCv(BaseModel):
    cv: str | None


@router.get("/latest", response_model=LatestCv)
def latest_cv(db: Session = Depends(get_db)) -> LatestCv:
    """The CV of the newest Interview that has one, so Setup can pre-fill it (spec: CV)."""
    cv = db.scalars(
        select(Interview.cv)
        .where(Interview.cv.is_not(None))
        .order_by(Interview.created_at.desc(), Interview.id.desc())
        .limit(1)
    ).first()
    return LatestCv(cv=cv)
