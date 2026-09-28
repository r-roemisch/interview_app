"""Persona: the name, job title and voice the interviewer presents as (CONTEXT.md)."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from interview_app.llm import Message
from interview_app.models import (
    DEFAULT_PERSONA_NAME,
    DEFAULT_PERSONA_TITLE,
    DEFAULT_PERSONA_VOICE,
    PERSONA_VOICES,
    Interview,
)

# An unknown voice fails validation, so the whole Persona falls back (spec: voice-interview).
Voice = Literal[tuple(PERSONA_VOICES)]  # type: ignore[valid-type]


class Persona(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    voice: Voice


# Used whenever the Persona call fails: the Persona must never block an Interview (spec).
DEFAULT_PERSONA = Persona(name=DEFAULT_PERSONA_NAME, title=DEFAULT_PERSONA_TITLE, voice=DEFAULT_PERSONA_VOICE)


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
            "Also pick the speaking voice that best fits the name, from these voices:",
            *(f"- {voice}: {description}" for voice, description in PERSONA_VOICES.items()),
            "Return ONLY a JSON object matching this schema, with no prose before or after it:",
            json.dumps(persona_schema()),
        ]
    )
    job = f"Job: {interview.title}\nSeniority: {interview.seniority.value}{industry}"
    return [{"role": "system", "content": system}, {"role": "user", "content": job}]
