"""JEV Judge: one JEV call, mapped to an Evaluation (ADR-0003). JEV writes no text."""

from __future__ import annotations

import logging

from interview_app.jev import Answer, JevClient
from interview_app.llm import LLMUnavailable
from interview_app.models import Evaluation, Interview, MessageRole, Verdict
from interview_app.prompts.jev_judge import (
    CHECKLIST,
    OVERALL_LEVELS,
    STAR_PARTS,
    check_key,
    questions_for_jev,
    star_key,
    state_for_jev,
)

log = logging.getLogger(__name__)


def evaluate(jev: JevClient, interview: Interview) -> Evaluation | None:
    """The JEV Evaluation, or None when JEV failed or answered something unusable."""
    try:
        answers = jev.decide(state_for_jev(interview), questions_for_jev(interview))
        return to_evaluation(interview, answers)
    except (LLMUnavailable, KeyError, TypeError, ValueError) as exc:
        log.error("JEV Judge failed for interview %s: %s", interview.id, exc)
        return None


def to_evaluation(interview: Interview, answers: dict[str, Answer]) -> Evaluation:
    answer_positions = [m.position for m in interview.messages if m.role == MessageRole.ANSWER]
    breakdowns = []
    for n, position in enumerate(answer_positions, start=1):
        breakdown: dict = {"position": position}
        for part in STAR_PARTS:
            a = answers[star_key(n, part)]
            # JEV's score runs 0-4 over the five levels; a rating runs 1-5.
            breakdown[part] = {"rating": _clamp(round(a["score"]) + 1, 1, 5), "comment": None, "confidence": a["confidence"]}
        breakdowns.append(breakdown)

    checklist = [{"check": check, "probability": answers[check_key(i)]["noul"]} for i, (check, _) in enumerate(CHECKLIST)]
    # The three checks JEV was least sure were met, weakest first: always exactly three.
    weakest = sorted(range(len(CHECKLIST)), key=lambda i: checklist[i]["probability"])[:3]

    overall, verdict = answers["overall"], answers["verdict"]
    return Evaluation(
        overall_score=_clamp(round(overall["score"] / (len(OVERALL_LEVELS) - 1) * 100), 0, 100),
        overall_confidence=overall["confidence"],
        justification=None,
        verdict=Verdict(verdict["choice"]),
        verdict_confidence=verdict["confidence"],
        improvement_points=[CHECKLIST[i][1] for i in weakest],
        star_breakdowns=breakdowns,
        checklist=checklist,
    )


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
