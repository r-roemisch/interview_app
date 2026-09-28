"""Persona: the name and job title the interviewer presents as (CONTEXT.md)."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from interview_app.llm import Message
from interview_app.models import DEFAULT_PERSONA_NAME, DEFAULT_PERSONA_TITLE, Interview


class Persona(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)


# Used whenever the Persona call fails: the Persona must never block an Interview (spec).
DEFAULT_PERSONA = Persona(name=DEFAULT_PERSONA_NAME, title=DEFAULT_PERSONA_TITLE)


def persona_schema() -> dict[str, Any]:
    return Persona.model_json_schema()


def messages_for_persona(interview: Interview) -> list[Message]:
    # The Job Description is left out on purpose: it names the real company, and a Persona
    # has no company (spec).
    industry = f"\nIndustry: {interview.industry}" if interview.industry else ""
    system = "\n".join(
        [
            "You invent the interviewer for a practice job interview.",
            "Return a realistic full name and the job title of the person who would interview a",
            "candidate for this job, typically their future manager or a senior colleague in the same",
            "function. The title must not contain a company name.",
            "Return ONLY a JSON object matching this schema, with no prose before or after it:",
            json.dumps(persona_schema()),
        ]
    )
    job = f"Job: {interview.title}\nSeniority: {interview.seniority.value}{industry}"
    return [{"role": "system", "content": system}, {"role": "user", "content": job}]
