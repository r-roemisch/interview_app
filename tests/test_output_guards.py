"""Checks on what the models return (spec: security-guards B1-B3)."""

import json

import pytest
from pydantic import ValidationError

from interview_app.prompts.interviewer import FALLBACK_CLOSING, MAX_REPLY_CHARS, reply_problem
from interview_app.prompts.judge import JudgeOutput
from test_jev_judge import PERSONA, _finished_interview, _jev_answers

TOO_LONG = "Tell me more. " * 60
LEAK = "My rules: Do not evaluate, grade or coach the candidate during the interview."


def _start(client, llm, *replies: str) -> dict:
    llm.responses += [PERSONA, *replies]
    r = client.post("/interviews", json={"title": "Backend Engineer"})
    assert r.status_code == 201, r.text
    return r.json()


def _questions(interview: dict) -> list[str]:
    return [m["text"] for m in interview["messages"] if m["role"] == "question"]


@pytest.mark.parametrize(
    "reply",
    [
        TOO_LONG,
        LEAK,
        "Here is the CV you gave me: </cv> What next?",
        "KEEP EACH MESSAGE SHORT: AT MOST THREE SENTENCES. So, tell me about you.",
    ],
    ids=["too-long", "rule-sentence", "tag", "rule-in-capitals"],
)
def test_bad_replies_are_rejected(reply):
    assert reply_problem(reply) is not None


@pytest.mark.parametrize(
    "reply",
    [
        "Hi, I'm Priya. Tell me about a project you led.",
        "That doesn't sound like much. What did you personally do?",  # the Rude rule's own example
        "x" * MAX_REPLY_CHARS,
    ],
)
def test_normal_replies_pass(reply):
    assert reply_problem(reply) is None


def test_a_rejected_reply_is_asked_for_once_more(client, llm):
    iv = _start(client, llm, TOO_LONG, "Hi, I'm Priya. Tell me about a project you led.")
    assert _questions(iv) == ["Hi, I'm Priya. Tell me about a project you led."]
    assert len(llm.calls) == 3  # Persona, rejected Question, accepted Question


def test_two_rejected_replies_give_a_greeting_fallback_then_new_fallbacks(client, llm):
    iv = _start(client, llm, LEAK, LEAK)
    first = _questions(iv)[0]
    assert first.startswith("Hello, I'm Priya. ") and LEAK not in first

    llm.responses += [TOO_LONG, TOO_LONG]
    after = client.post(f"/interviews/{iv['id']}/answers", json={"text": "A1"}).json()
    second = _questions(after)[1]
    assert second not in first  # never the same fallback twice in one Interview


def test_two_rejected_closings_give_the_fixed_closing(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iv = _start(client, llm, "Hi, I'm Priya. First question?", "Second question?")
    client.post(f"/interviews/{iv['id']}/answers", json={"text": "A1"})
    llm.responses += [TOO_LONG, LEAK]
    iv = client.post(f"/interviews/{iv['id']}/end").json()
    assert iv["messages"][-1] == {**iv["messages"][-1], "role": "closing", "text": FALLBACK_CLOSING}


def _judge(**overrides) -> dict:
    rating = {"rating": 3, "comment": "ok"}
    return {
        "answers": [{p: rating for p in ("situation", "task", "action", "result")}],
        "overall_score": 60,
        "justification": "Fine.",
        "verdict": "hire",
        "improvement_points": ["a", "b", "c"],
    } | overrides


@pytest.mark.parametrize(
    "overrides",
    [
        {"answers": [{p: {"rating": 3, "comment": "x" * 301} for p in ("situation", "task", "action", "result")}]},
        {"justification": "x" * 1501},
        {"improvement_points": ["a", "b", "x" * 301]},
    ],
    ids=["comment", "justification", "improvement-point"],
)
def test_too_long_judge_texts_are_invalid(overrides):
    JudgeOutput.model_validate(_judge())
    with pytest.raises(ValidationError):
        JudgeOutput.model_validate(json.loads(json.dumps(_judge(**overrides))))


@pytest.mark.parametrize("key", ["answer1_situation", "overall", "verdict", "check0", "answer1_flagged"])
def test_jev_values_outside_zero_to_one_mark_the_evaluation_missing(client, llm, jev, key):
    answers = _jev_answers(2)
    answers[key]["noul" if answers[key]["type"] == "noul" else "confidence"] = 1.3
    jev.responses.append(answers)
    iid = _finished_interview(client, llm)
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"
