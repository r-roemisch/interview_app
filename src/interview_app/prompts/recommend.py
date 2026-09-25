"""Recommended Settings: infer Job fields from a pasted Job Description."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from interview_app.llm import Message
from interview_app.models import Seniority


class RecommendedSettings(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=200)
    seniority: Seniority = Seniority.MID

    @field_validator("seniority", mode="before")
    @classmethod
    def _tolerant_seniority(cls, v: Any) -> Any:
        """Free models say 'Senior', 'mid-level', 'lead'... Anything unrecognised becomes mid."""
        if isinstance(v, str):
            s = v.strip().lower()
            for member in Seniority:
                if s.startswith(member.value):
                    return member
        return Seniority.MID

    @field_validator("industry", mode="before")
    @classmethod
    def _blank_industry_is_none(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.strip():
            return None
        return v


def recommended_settings_schema() -> dict[str, Any]:
    return RecommendedSettings.model_json_schema()


def messages_for_recommendation(job_description: str) -> list[Message]:
    system = "\n".join(
        [
            "You extract structured fields from a job posting.",
            "Return the job title, the industry of the hiring company (or null if unclear), and the",
            "seniority of the role as exactly one of: junior, mid, senior.",
            "Return ONLY a JSON object matching this schema, with no prose before or after it:",
            json.dumps(recommended_settings_schema()),
        ]
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "<job_description>\n" + job_description.strip() + "\n</job_description>"},
    ]
