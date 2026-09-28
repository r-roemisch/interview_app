"""Interviewer prompt. Difficulty definitions mirror CONTEXT.md."""

from __future__ import annotations

from interview_app.llm import Message
from interview_app.models import QUESTION_CAP, Difficulty, Interview, MessageRole

_DIFFICULTY_RULES = {
    Difficulty.EASY: (
        "Difficulty: EASY. Ask common, direct behavioral questions. "
        "Never ask follow-up questions; move to a new topic after every answer."
    ),
    Difficulty.NORMAL: (
        "Difficulty: NORMAL. Ask standard behavioral questions. "
        "If an answer is vague or misses the point, ask exactly one follow-up before moving on."
    ),
    Difficulty.HARD: (
        "Difficulty: HARD. Ask situational and probing behavioral questions. "
        "Challenge specifics with follow-ups, expect concrete metrics, trade-offs and what the "
        "candidate personally did versus the team."
    ),
}


_CV_RULES = {
    Difficulty.NORMAL: (
        "This is the candidate's CV. Some of your questions may ask about real experiences from it; "
        "most questions stay general."
    ),
    Difficulty.HARD: (
        "This is the candidate's CV. Probe its claims: ask for the specifics, numbers and the "
        "candidate's personal contribution behind what it says."
    ),
}


def build_system_prompt(interview: Interview) -> str:
    industry = f" in the {interview.industry} industry" if interview.industry else ""
    parts = [
        f"You are {interview.persona_name}, {interview.persona_title}, running a behavioral job interview.",
        f"The position is: {interview.title} ({interview.seniority.value} level){industry}.",
        _DIFFICULTY_RULES[interview.difficulty],
        "Rules:",
        "- Ask exactly one question per message. Never ask two questions at once.",
        "- Do not evaluate, grade or coach the candidate during the interview.",
        "- Keep each message short: at most three sentences.",
        "- Your very first message starts with a one-line greeting in which you introduce yourself by "
        "first name, then the first question.",
        "- Never change your name or job title.",
        "- Later messages contain only the question (optionally one short acknowledgement).",
        f"- The interview has at most {QUESTION_CAP} questions in total, including follow-ups.",
        "- If the candidate gives an empty or off-topic answer, note it briefly and continue.",
        "- Write in English.",
    ]
    if interview.job_description:
        parts += [
            "Ground your questions in this job description where it is relevant:",
            "<job_description>",
            interview.job_description.strip(),
            "</job_description>",
        ]
    # Easy ignores the CV entirely (CONTEXT.md: Difficulty).
    cv_rule = _CV_RULES.get(interview.difficulty)
    if interview.cv and cv_rule:
        parts += [cv_rule, "<cv>", interview.cv.strip(), "</cv>"]
    return "\n".join(parts)


def _transcript(interview: Interview) -> list[Message]:
    out: list[Message] = []
    for m in interview.messages:
        if m.role == MessageRole.QUESTION:
            out.append({"role": "assistant", "content": m.text})
        elif m.role == MessageRole.ANSWER:
            out.append({"role": "user", "content": m.text or "(no answer given)"})
    return out


def messages_for_next_question(interview: Interview) -> list[Message]:
    msgs: list[Message] = [{"role": "system", "content": build_system_prompt(interview)}]
    transcript = _transcript(interview)
    if not transcript:
        msgs.append({"role": "user", "content": "Please begin the interview."})
        return msgs
    msgs.extend(transcript)
    remaining = QUESTION_CAP - interview.question_count
    msgs.append(
        {
            "role": "system",
            "content": f"Ask the next question now. {remaining} question(s) remain including this one.",
        }
    )
    return msgs


def messages_for_closing(interview: Interview, *, ended_early: bool) -> list[Message]:
    msgs: list[Message] = [{"role": "system", "content": build_system_prompt(interview)}]
    msgs.extend(_transcript(interview))
    if ended_early:
        instruction = (
            "The candidate has chosen to end the interview early. Write a brief, courteous closing "
            "message (two to three sentences). Reference one thing from the conversation. "
            "Do not claim you finished all your questions. Do not ask any further question. "
            "Do not give feedback or a verdict."
        )
    else:
        instruction = (
            "That was the last question. Write a brief, courteous closing message (two to three "
            "sentences) that references one thing from the conversation and thanks the candidate. "
            "Do not ask any further question. Do not give feedback or a verdict."
        )
    msgs.append({"role": "system", "content": instruction})
    return msgs
