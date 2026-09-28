import json

import pytest

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "Kore"})
CV = "Led the billing migration at Acme, cutting costs by 30%."


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


def _start(client, llm, **overrides) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. Tell me about a project you led."]
    body = {"title": "Backend Engineer", "seniority": "senior"} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _prompt(call) -> str:
    return "\n".join(m["content"] for m in call["messages"])


def test_cv_is_stored_but_not_returned(client, llm, db):
    from interview_app.models import Interview

    data = _start(client, llm, cv=f"  {CV}  ")
    assert "cv" not in data
    assert db.get(Interview, data["id"]).cv == CV


def test_blank_cv_is_stored_as_none(client, llm, db):
    from interview_app.models import Interview

    data = _start(client, llm, cv="   ")
    assert db.get(Interview, data["id"]).cv is None


def test_cv_longer_than_limit_is_rejected(client):
    r = client.post("/interviews", json={"title": "Backend Engineer", "cv": "x" * 20_001})
    assert r.status_code == 422


def test_practice_again_copies_cv(client, llm, db):
    from interview_app.models import Interview

    iid = _start(client, llm, cv=CV)["id"]
    llm.responses += [PERSONA, "Hello again. First question?"]
    r = client.post(f"/interviews/{iid}/practice-again")
    assert r.status_code == 201, r.text
    assert db.get(Interview, r.json()["id"]).cv == CV


def test_latest_cv_is_the_newest_interview_with_one(client, llm):
    assert client.get("/cv/latest").json() == {"cv": None}

    _start(client, llm, cv="Old CV")
    _start(client, llm, cv=CV)
    _start(client, llm)  # no CV: does not hide the previous one
    assert client.get("/cv/latest").json() == {"cv": CV}


@pytest.mark.parametrize(
    ("difficulty", "cv_in_prompt", "probes"),
    [("easy", False, False), ("normal", True, False), ("hard", True, True)],
)
def test_interviewer_uses_cv_by_difficulty(client, llm, difficulty, cv_in_prompt, probes):
    iid = _start(client, llm, cv=CV, difficulty=difficulty)["id"]
    llm.responses += ["Q2?", "Thanks, bye.", _judge_reply(1)]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    client.post(f"/interviews/{iid}/end")

    first_question, next_question, closing = llm.calls[1], llm.calls[2], llm.calls[3]
    for call in (first_question, next_question, closing):
        system = call["messages"][0]["content"]
        assert (CV in system) is cv_in_prompt
        assert ("Probe its claims" in system) is probes


def test_cv_never_reaches_persona_judge_or_recommended_settings(client, llm):
    iid = _start(client, llm, cv=CV, difficulty="hard")["id"]
    llm.responses += ["Q2?", "Thanks, bye.", _judge_reply(1)]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    assert client.post(f"/interviews/{iid}/end").status_code == 200
    assert client.get(f"/interviews/{iid}/evaluation").status_code == 200

    persona_call, judge_call = llm.calls[0], llm.calls[-1]
    assert judge_call["json_schema"] is not None and "hiring manager" in _prompt(judge_call)
    assert CV not in _prompt(persona_call)
    assert CV not in _prompt(judge_call)

    llm.responses.append(json.dumps({"title": "Backend Engineer", "industry": None, "seniority": "senior"}))
    assert client.post("/recommend-settings", json={"job_description": "We need a backend engineer."}).status_code == 200
    assert CV not in _prompt(llm.calls[-1])
