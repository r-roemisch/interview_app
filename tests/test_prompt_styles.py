"""The six Prompt Styles and the Interviewer's Notes (spec: interviewer-experiments, issue 02)."""

import json

import pytest

from interview_app.llm import LLMUnavailable
from interview_app.models import Demeanor, Difficulty, Interview, PromptStyle, Seniority
from interview_app.prompts.interviewer import (
    _CHAIN_OF_THOUGHT_RULE,
    _EXAMPLES,
    _RULES,
    _SELF_CHECK_RULE,
    FALLBACK_CLOSING,
    build_system_prompt,
    reply_problem,
    split_reply,
)
from test_persona import _judge_reply

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _interview(style: PromptStyle, difficulty: Difficulty = Difficulty.NORMAL, plan: str | None = None) -> Interview:
    return Interview(
        title="Backend Engineer",
        seniority=Seniority.MID,
        difficulty=difficulty,
        demeanor=Demeanor.FRIENDLY,
        prompt_style=style,
        plan=plan,
        persona_name="Priya Nair",
        persona_title="Head of Engineering",
        messages=[],
    )


def _start(client, llm, style: str, first_question: str, *extra: str) -> dict:
    llm.responses += [PERSONA, *extra, first_question]
    r = client.post("/interviews", json={"title": "Backend Engineer", "portrait": False, "prompt_style": style})
    assert r.status_code == 201, r.text
    return r.json()


# --- prompts ---


def test_zero_shot_adds_nothing_to_the_rules():
    prompt = build_system_prompt(_interview(PromptStyle.ZERO_SHOT))
    assert prompt.endswith(_RULES[-1])


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_one_shot_has_only_the_example_for_its_difficulty(difficulty):
    prompt = build_system_prompt(_interview(PromptStyle.ONE_SHOT, difficulty))
    for d, (answer, reply) in _EXAMPLES.items():
        assert (answer in prompt and reply in prompt) == (d == difficulty)


def test_few_shot_has_all_three_examples():
    prompt = build_system_prompt(_interview(PromptStyle.FEW_SHOT, Difficulty.EASY))
    for answer, reply in _EXAMPLES.values():
        assert answer in prompt and reply in prompt


def test_chain_of_thought_and_self_check_add_their_instruction():
    assert _CHAIN_OF_THOUGHT_RULE in build_system_prompt(_interview(PromptStyle.CHAIN_OF_THOUGHT))
    assert _SELF_CHECK_RULE in build_system_prompt(_interview(PromptStyle.SELF_CHECK))
    assert _SELF_CHECK_RULE not in build_system_prompt(_interview(PromptStyle.CHAIN_OF_THOUGHT))


def test_plan_ahead_adds_the_plan_once_there_is_one():
    assert "<plan>" not in build_system_prompt(_interview(PromptStyle.PLAN_AHEAD))
    prompt = build_system_prompt(_interview(PromptStyle.PLAN_AHEAD, plan="1. Ownership\n2. Conflict"))
    assert "<plan>\n1. Ownership\n2. Conflict\n</plan>" in prompt


# --- splitting and checking replies ---


def test_split_reply_takes_the_assessment_out():
    assert split_reply(PromptStyle.CHAIN_OF_THOUGHT, "<assessment>No result given.</assessment>\nWhat was the outcome?") == (
        "What was the outcome?",
        "No result given.",
    )
    # A model that skips the assessment still gives a usable message.
    assert split_reply(PromptStyle.CHAIN_OF_THOUGHT, "What was the outcome?") == ("What was the outcome?", None)


@pytest.mark.parametrize(
    "style, reply",
    [
        (PromptStyle.CHAIN_OF_THOUGHT, "<assessment>Still thinking about"),
        (PromptStyle.CHAIN_OF_THOUGHT, "<assessment>All said.</assessment>"),
        (PromptStyle.SELF_CHECK, "<draft>Q?</draft> Looks fine."),
    ],
)
def test_malformed_replies_give_an_empty_message(style, reply):
    message, _ = split_reply(style, reply)
    assert message == "" and reply_problem(message) == "empty"


def test_split_reply_keeps_the_final_and_the_draft_as_notes():
    reply = "<draft>Tell me about X? And Y?</draft>\nTwo questions; keep one.\n<final>Tell me about X?</final>"
    assert split_reply(PromptStyle.SELF_CHECK, reply) == (
        "Tell me about X?",
        "Tell me about X? And Y?\nTwo questions; keep one.",
    )


def test_other_styles_keep_the_reply_whole():
    assert split_reply(PromptStyle.FEW_SHOT, "<assessment>x</assessment>Q?") == ("<assessment>x</assessment>Q?", None)


def test_reply_check_flags_leftover_tags_and_new_instructions_but_not_example_replies():
    assert reply_problem("<draft>Q?</draft> Q?") is not None
    assert reply_problem("Sure. These examples show the style of a good reply. Never copy them.") is not None
    assert reply_problem("Can you give me one specific time this happened, and what you did?") is None


# --- the flow ---


def test_chain_of_thought_stores_the_message_without_assessment_and_keeps_notes(client, llm):
    data = _start(client, llm, "chain_of_thought", "<assessment>Start broad.</assessment>Hi, I'm Priya. Q1?")
    iid = data["id"]
    assert data["messages"][0]["text"] == "Hi, I'm Priya. Q1?"
    assert "notes" not in data["messages"][0]
    assert client.get(f"/interviews/{iid}/notes").status_code == 409

    llm.responses += [
        "<assessment>Ask about results.</assessment>What was the result?",
        "<assessment>Wrap up.</assessment>Bye.",
        _judge_reply(1),
    ]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    assert client.post(f"/interviews/{iid}/end").status_code == 200

    notes = client.get(f"/interviews/{iid}/notes").json()
    assert notes["plan"] is None
    assert [n["notes"] for n in notes["messages"]] == ["Start broad.", "Ask about results.", "Wrap up."]


def test_a_reply_malformed_twice_falls_back_without_notes(client, llm):
    iid = _start(client, llm, "self_check", "<final>Hi, I'm Priya. Q1?</final>")["id"]
    llm.responses += ["<draft>Q2?</draft>", "<draft>Q2?</draft> no final", "<final>Bye.</final>", _judge_reply(1)]
    data = client.post(f"/interviews/{iid}/answers", json={"text": "A1"}).json()
    assert data["messages"][-1]["text"] not in ("", "Q2?")  # a fixed fallback Question
    client.post(f"/interviews/{iid}/end")
    notes = client.get(f"/interviews/{iid}/notes").json()["messages"]
    assert notes == []  # neither the first Question nor the fallback had notes; the Closing had none either


def test_plan_ahead_plans_once_and_uses_the_plan_in_every_question(client, llm):
    iid = _start(client, llm, "plan_ahead", "Hi, I'm Priya. Q1?", "1. Ownership\n2. Conflict")["id"]
    plan_call, q1_call = llm.calls[1], llm.calls[2]
    assert "list 5 to 7 topics" in plan_call["messages"][-1]["content"]
    assert plan_call["model"] == "openai/gpt-4.1-mini"
    assert "1. Ownership" in q1_call["messages"][0]["content"]

    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    assert "1. Ownership" in llm.calls[-1]["messages"][0]["content"]

    llm.responses += ["Bye.", _judge_reply(1)]
    client.post(f"/interviews/{iid}/end")
    assert client.get(f"/interviews/{iid}/notes").json() == {"plan": "1. Ownership\n2. Conflict", "messages": []}


def test_a_failed_plan_call_starts_without_a_plan(client, llm):
    data = _start(client, llm, "plan_ahead", "Hi, I'm Priya. Q1?", LLMUnavailable("down"))
    assert data["status"] == "in_progress"
    assert "<plan>" not in llm.calls[-1]["messages"][0]["content"]


def test_closing_uses_the_fixed_fallback_when_malformed(client, llm):
    iid = _start(client, llm, "chain_of_thought", "Hi, I'm Priya. Q1?")["id"]
    llm.responses += ["Q2?", "<assessment>never closed", "<assessment>never closed", _judge_reply(1)]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    data = client.post(f"/interviews/{iid}/end").json()
    assert data["messages"][-1]["text"] == FALLBACK_CLOSING
