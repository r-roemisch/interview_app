import json

import pytest

from interview_app.llm import LLMUnavailable

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _judge_reply(answers: int) -> str:
    r = {"rating": 3, "comment": "ok"}
    return json.dumps(
        {
            "answers": [{"situation": r, "task": r, "action": r, "result": r}] * answers,
            "overall_score": 60,
            "justification": "Fine.",
            "verdict": "hire",
            "improvement_points": ["a", "b", "c"],
        }
    )


def _start(client, llm, persona_reply=PERSONA, **overrides) -> dict:
    llm.responses += [persona_reply, "Hi, I'm Priya. Tell me about a project you led."]
    body = {"title": "Backend Engineer", "seniority": "senior"} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_persona_is_stored_and_returned_but_not_in_history(client, llm):
    data = _start(client, llm, industry="fintech", job_description="Acme Corp builds payment APIs.")
    assert (data["persona_name"], data["persona_title"]) == ("Priya Nair", "Head of Engineering")

    again = client.get(f"/interviews/{data['id']}").json()
    assert (again["persona_name"], again["persona_title"]) == ("Priya Nair", "Head of Engineering")

    row = client.get("/interviews").json()[0]
    assert "persona_name" not in row and "persona_title" not in row

    persona_call = llm.calls[0]
    assert persona_call["json_schema"] is not None
    prompt = "\n".join(m["content"] for m in persona_call["messages"])
    assert "Backend Engineer" in prompt and "senior" in prompt and "fintech" in prompt
    assert "Acme Corp" not in prompt  # a Persona has no company


def test_persona_reaches_interviewer_but_not_judge(client, llm):
    iid = _start(client, llm)["id"]
    first_question_system = llm.calls[1]["messages"][0]["content"]
    assert "You are Priya Nair, Head of Engineering" in first_question_system
    assert "introduce yourself by first name" in first_question_system

    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    assert "Priya Nair" in llm.calls[-1]["messages"][0]["content"]

    llm.responses += ["Thanks, bye.", _judge_reply(1)]
    assert client.post(f"/interviews/{iid}/end").status_code == 200
    closing_call, judge_call = llm.calls[-2], llm.calls[-1]
    assert "Priya Nair" in closing_call["messages"][0]["content"]
    assert judge_call["json_schema"] is not None
    # The transcript may mention the name (the greeting does); the Persona fields must not.
    assert all("Head of Engineering" not in m["content"] for m in judge_call["messages"])
    assert "Priya Nair" not in judge_call["messages"][0]["content"]


@pytest.mark.parametrize(
    "persona_reply",
    [
        LLMUnavailable("down"),
        "Sure! Your interviewer is Priya.",
        json.dumps({"name": "Priya Nair"}),
        json.dumps({"name": "  ", "title": "Head of Engineering", "voice": "coral"}),
        json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "darth"}),
        json.dumps({"name": "Priya Nair", "title": "Head of Engineering"}),
    ],
    ids=["unavailable", "not-json", "missing-title", "blank-name", "unknown-voice", "missing-voice"],
)
def test_failed_persona_call_falls_back_and_interview_still_starts(client, llm, persona_reply):
    data = _start(client, llm, persona_reply=persona_reply)
    assert (data["persona_name"], data["persona_title"]) == ("Alex Morgan", "Hiring Manager")
    assert data["persona_voice"] == "cedar"
    assert data["question_count"] == 1
    assert len(llm.calls) == 2  # no retry of the Persona call
    assert "You are Alex Morgan, Hiring Manager" in llm.calls[1]["messages"][0]["content"]


def test_code_fenced_persona_is_accepted(client, llm):
    data = _start(client, llm, persona_reply="```json\n" + PERSONA + "\n```")
    assert data["persona_name"] == "Priya Nair"


def test_practice_again_gets_a_fresh_persona(client, llm):
    iid = _start(client, llm)["id"]

    llm.responses += [json.dumps({"name": "Tom Berg", "title": "VP Engineering", "voice": "ash"}), "Hi, I'm Tom. Q1?"]
    r = client.post(f"/interviews/{iid}/practice-again")
    assert r.status_code == 201, r.text
    new = r.json()
    assert (new["persona_name"], new["persona_title"]) == ("Tom Berg", "VP Engineering")
    assert llm.calls[-2]["json_schema"] is not None  # a new Persona call, not a copy

    old = client.get(f"/interviews/{iid}").json()
    assert old["persona_name"] == "Priya Nair"


def test_persona_voice_is_picked_from_the_list_and_stored(client, llm):
    data = _start(client, llm)
    assert data["persona_voice"] == "coral"
    assert "persona_voice" not in client.get("/interviews").json()[0]

    persona_call = llm.calls[0]
    assert persona_call["json_schema"]["properties"]["voice"]["enum"] == ["marin", "coral", "sage", "cedar", "ash", "echo"]
    assert "- ash: firm, male-sounding" in persona_call["messages"][0]["content"]


def test_voice_interview_is_stored_and_copied_with_a_fresh_persona_voice(client, llm):
    assert _start(client, llm)["voice_interview"] is False

    iid = _start(client, llm, voice_interview=True)["id"]
    assert client.get(f"/interviews/{iid}").json()["voice_interview"] is True

    llm.responses += [json.dumps({"name": "Tom Berg", "title": "VP Engineering", "voice": "ash"}), "Hi, I'm Tom. Q1?"]
    again = client.post(f"/interviews/{iid}/practice-again").json()
    assert (again["voice_interview"], again["persona_voice"]) == (True, "ash")
