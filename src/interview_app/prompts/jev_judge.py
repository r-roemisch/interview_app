"""JEV Judge: the state and typed questions sent to JEV, and the Checklist (ADR-0003)."""

from __future__ import annotations

from interview_app.jev import Question, choice, score, yes_no
from interview_app.models import Interview
from interview_app.prompts.judge import job_block, transcript_block

# (check asked as yes/no about the whole Interview, Improvement Point used when it is among the weakest)
CHECKLIST: list[tuple[str, str]] = [
    (
        "Results are quantified with numbers or clear outcomes",
        "End every story with a measurable result: a number, a time saved, a before and after.",
    ),
    (
        'The candidate says "I" when describing their own actions',
        "Say \"I\" for what you personally did, and keep the team's work separate.",
    ),
    (
        "The Situation and Task are set up briefly",
        "Keep the Situation and Task to two sentences and spend your time on the Actions.",
    ),
    (
        "Answers address the question that was asked",
        "Answer the question asked before adding anything else; restate it if it helps you focus.",
    ),
    (
        "Examples are specific real events, not hypotheticals",
        "Use one specific real example instead of describing what you would usually do.",
    ),
    (
        "Answers include what was learned or would be done differently",
        "Close with what you learned or what you would do differently next time.",
    ),
    ("Examples relate to the skills the job needs", "Pick examples that show the skills this job asks for."),
    (
        "Answers are concise and structured",
        "Keep answers under two minutes and follow Situation, Task, Action, Result in order.",
    ),
]

STAR_PARTS = {
    "situation": "the context of the example",
    "task": "the candidate's responsibility or goal",
    "action": "what the candidate personally did",
    "result": "the outcome, ideally measurable",
}
STAR_LEVELS = ["1: absent or very weak", "2: weak", "3: adequate", "4: good", "5: excellent"]
OVERALL_LEVELS = [
    "Very poor", "Poor", "Weak", "Below average", "Average",
    "Above average", "Good", "Strong", "Very strong", "Outstanding",
]  # fmt: skip
VERDICTS = {
    "strong_hire": "Exceptional answers; a real interviewer would push to hire",
    "hire": "Solid answers; a real interviewer would hire",
    "no_hire": "Answers not convincing enough to hire",
}


def star_key(answer_no: int, part: str) -> str:
    return f"answer{answer_no}_{part}"


def check_key(index: int) -> str:
    return f"check{index}"


def state_for_jev(interview: Interview) -> str:
    """The same Job and transcript the LLM Judge sees. No CV, no Persona."""
    return f"POSITION\n{job_block(interview)}\n\nTRANSCRIPT\n{transcript_block(interview)}"


def questions_for_jev(interview: Interview) -> dict[str, Question]:
    questions: dict[str, Question] = {}
    for n in range(1, interview.answer_count + 1):
        for part, meaning in STAR_PARTS.items():
            questions[star_key(n, part)] = score(
                f"Rate the {part.title()} ({meaning}) in CANDIDATE answer {n}, using the STAR method. "
                "An empty or off-topic answer is 1.",
                STAR_LEVELS,
            )
    questions["overall"] = score(
        "How strong is this candidate overall for the position, judged on the STAR structure of all "
        "answers and their fit to the job?",
        OVERALL_LEVELS,
    )
    questions["verdict"] = choice("What hiring decision would a real interviewer make?", VERDICTS)
    for i, (check, _) in enumerate(CHECKLIST):
        questions[check_key(i)] = yes_no(f"Across the whole interview: {check}.")
    return questions
