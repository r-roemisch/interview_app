"""Interviewer Model and Prompt Style choice (spec: interviewer-experiments, issue 01)."""

import json

from test_persona import _judge_reply

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _start(client, llm, **overrides) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. Tell me about a project you led."]
    body = {"title": "Backend Engineer", "portrait": False} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_defaults_are_the_baseline_model_and_zero_shot(client, llm):
    data = _start(client, llm)
    assert data["interviewer_model"] == "openai/gpt-4.1-mini"
    assert data["prompt_style"] == "zero_shot"


def test_questions_and_closing_use_the_interviewer_model_but_persona_and_judge_do_not(client, llm):
    iid = _start(client, llm, interviewer_model="anthropic/claude-sonnet-5.5", prompt_style="few_shot")["id"]
    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    llm.responses += ["Thanks, bye.", _judge_reply(1)]
    assert client.post(f"/interviews/{iid}/end").status_code == 200

    persona, q1, q2, closing, judge = llm.calls
    assert persona["model"] is None and judge["model"] is None
    assert {q1["model"], q2["model"], closing["model"]} == {"anthropic/claude-sonnet-5.5"}
    stored = client.get(f"/interviews/{iid}").json()
    assert stored["interviewer_model"] == "anthropic/claude-sonnet-5.5"
    assert stored["prompt_style"] == "few_shot"


def test_unknown_model_or_prompt_style_is_rejected(client, llm):
    assert client.post("/interviews", json={"title": "X", "interviewer_model": "openai/gpt-5.5"}).status_code == 422
    assert client.post("/interviews", json={"title": "X", "prompt_style": "tree_of_thought"}).status_code == 422
    assert llm.calls == []


def test_practice_again_copies_both(client, llm):
    iid = _start(client, llm, interviewer_model="google/gemma-4-31b-it", prompt_style="few_shot")["id"]
    llm.responses += [PERSONA, "Hi. Q1?"]
    again = client.post(f"/interviews/{iid}/practice-again").json()
    assert again["interviewer_model"] == "google/gemma-4-31b-it"
    assert again["prompt_style"] == "few_shot"


def test_history_rows_carry_both(client, llm):
    _start(client, llm, interviewer_model="openai/gpt-5-nano", prompt_style="chain_of_thought")
    row = client.get("/interviews").json()[0]
    assert row["interviewer_model"] == "openai/gpt-5-nano"
    assert row["prompt_style"] == "chain_of_thought"
