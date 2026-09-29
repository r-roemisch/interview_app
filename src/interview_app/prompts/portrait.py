"""Portrait prompt (CONTEXT.md: Portrait). Like the Persona call, it never sees the CV or the Job
Description: the Persona has no company."""

from __future__ import annotations

from interview_app.models import PERSONA_VOICES, Interview


def portrait_prompt(interview: Interview) -> str:
    # The face must match the voice the Persona speaks with ("female-sounding", "male-sounding").
    voice = PERSONA_VOICES.get(interview.persona_voice, "")
    person = "woman" if "female" in voice else "man" if "male" in voice else "person"
    industry = f" in the {interview.industry} industry" if interview.industry else ""
    return (
        # "Fictional": a named person otherwise reads as a real one, which image models may refuse.
        f"A photorealistic professional headshot of a fictional {person} named {interview.persona_name}, "
        f"who works as {interview.persona_title}{industry}. Head and shoulders, looking at the camera, friendly and "
        "professional expression, natural soft light, plain soft neutral background. "
        "No text, no logos, no watermark."
    )
