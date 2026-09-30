import json

import pytest

from interview_app.models import Demeanor, Difficulty, Interview, Seniority
from interview_app.prompts.interviewer import _RUDE_RULE, build_system_prompt
from interview_app.prompts.portrait import portrait_prompt
from test_jev_judge import _jev_answers
from test_persona import _judge_reply

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _start(client, llm, **overrides) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. Tell me about a project you led."]
    body = {"title": "Backend Engineer", "portrait": False} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _end(client, llm, iid: int, *judge_replies: str) -> tuple[dict, dict]:
    """Answer once and end early; returns the closing call and the Judge call."""
    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    llm.responses += ["Thanks, bye.", *judge_replies]
    assert client.post(f"/interviews/{iid}/end").status_code == 200
    return llm.calls[-1 - len(judge_replies)], llm.calls[-1] if judge_replies else {}


def _interview(demeanor: Demeanor, difficulty: Difficulty = Difficulty.NORMAL) -> Interview:
    return Interview(
        title="Backend Engineer",
        seniority=Seniority.MID,
        difficulty=difficulty,
        demeanor=demeanor,
        persona_name="Priya Nair",
        persona_title="Head of Engineering",
        persona_voice="coral",
        messages=[],
    )


def test_friendly_is_the_default_and_rude_is_stored(client, llm):
    assert _start(client, llm)["demeanor"] == "friendly"
    iid = _start(client, llm, demeanor="rude")["id"]
    assert client.get(f"/interviews/{iid}").json()["demeanor"] == "rude"


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_rude_rule_is_added_on_every_difficulty_and_friendly_is_unchanged(difficulty):
    rude = build_system_prompt(_interview(Demeanor.RUDE, difficulty))
    friendly = build_system_prompt(_interview(Demeanor.FRIENDLY, difficulty))
    assert "Demeanor: RUDE" in rude and "never swear" in rude
    assert "RUDE" not in friendly
    # Friendly is the prompt as it was before Demeanor existed: the rude one minus its rule.
    assert rude.replace(_RUDE_RULE + "\n", "") == friendly


def test_rude_rule_reaches_the_questions_and_the_closing(client, llm):
    iid = _start(client, llm, demeanor="rude")["id"]
    assert "Demeanor: RUDE" in llm.calls[1]["messages"][0]["content"]  # greeting + first Question
    closing_call, _ = _end(client, llm, iid, _judge_reply(1))
    assert "Demeanor: RUDE" in closing_call["messages"][0]["content"]


def test_rude_portrait_crosses_its_arms_and_friendly_smiles():
    rude = portrait_prompt(_interview(Demeanor.RUDE))
    friendly = portrait_prompt(_interview(Demeanor.FRIENDLY))
    assert "arms crossed" in rude and "stern and unimpressed" in rude and "friendly" not in rude
    assert "friendly and professional expression" in friendly and "arms crossed" not in friendly


def test_persona_and_llm_judge_never_see_the_demeanor(client, llm):
    iid = _start(client, llm, demeanor="rude")["id"]
    persona_call = llm.calls[0]
    _, judge_call = _end(client, llm, iid, _judge_reply(1))
    for call in (persona_call, judge_call):
        text = "\n".join(m["content"] for m in call["messages"]).lower()
        assert "rude" not in text and "demeanor" not in text


def test_jev_judge_never_sees_the_demeanor(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iid = _start(client, llm, demeanor="rude", judge="jev")["id"]
    _end(client, llm, iid)
    state = jev.calls[0]["state"].lower()
    assert "rude" not in state and "demeanor" not in state


def test_practice_again_copies_the_demeanor(client, llm):
    iid = _start(client, llm, demeanor="rude")["id"]
    llm.responses += [PERSONA, "Hi. Q1?"]
    assert client.post(f"/interviews/{iid}/practice-again").json()["demeanor"] == "rude"
