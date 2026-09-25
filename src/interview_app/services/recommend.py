from __future__ import annotations

import json

from pydantic import ValidationError

from interview_app.llm import LLMClient, strip_code_fence
from interview_app.prompts.recommend import (
    RecommendedSettings,
    messages_for_recommendation,
    recommended_settings_schema,
)


class RecommendationInvalid(Exception):
    pass


def recommend_settings(llm: LLMClient, job_description: str) -> RecommendedSettings:
    """One LLM call, one retry on unparsable output. Raises LLMUnavailable or RecommendationInvalid."""
    last_error = ""
    for _ in (1, 2):
        raw = llm.complete(messages_for_recommendation(job_description), json_schema=recommended_settings_schema())
        try:
            return RecommendedSettings.model_validate(json.loads(strip_code_fence(raw)))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
    raise RecommendationInvalid(last_error)
