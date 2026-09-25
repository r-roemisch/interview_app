from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from interview_app.llm import LLMClient, LLMUnavailable, get_llm_client
from interview_app.prompts.recommend import RecommendedSettings
from interview_app.services.recommend import RecommendationInvalid, recommend_settings

router = APIRouter(tags=["setup"])


class RecommendIn(BaseModel):
    job_description: str = Field(max_length=20_000)


@router.post("/recommend-settings", response_model=RecommendedSettings)
def post_recommend_settings(body: RecommendIn, llm: LLMClient = Depends(get_llm_client)) -> RecommendedSettings:
    if not body.job_description.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Job description is empty")
    try:
        return recommend_settings(llm, body.job_description)
    except LLMUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"The model is unavailable: {exc}") from exc
    except RecommendationInvalid as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "The model did not return usable settings; try again"
        ) from exc
