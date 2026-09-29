import json

from interview_app.llm import LLMUnavailable
from interview_app.models import Interview, Message

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


def _start(client, llm, **overrides):
    llm.responses += [PERSONA, "Hello! Tell me about a time you led a project."]
    body = {"title": "Backend Engineer", "seniority": "senior", "difficulty": "hard"} | overrides
    r = client.post("/interviews", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def test_start_returns_greeting_and_first_question(client, llm):
    data = _start(client, llm, industry="fintech", job_description="Build payment APIs.")
    assert data["status"] == "in_progress"
    assert data["question_count"] == 1
    assert data["messages"][0]["role"] == "question"
    assert data["messages"][0]["text"].startswith("Hello!")

    first_question_call = llm.calls[1]  # calls[0] creates the Persona
    system = first_question_call["messages"][0]["content"]
    assert "Backend Engineer" in system
    assert "senior level" in system
    assert "fintech" in system
    assert "Difficulty: HARD" in system
    assert "Build payment APIs." in system
    assert first_question_call["messages"][-1]["content"] == "Please begin the interview."


def test_title_is_required(client):
    r = client.post("/interviews", json={"title": ""})
    assert r.status_code == 422


def test_full_ten_question_run_ends_with_closing_and_judging(client, llm):
    data = _start(client, llm)
    iid = data["id"]
    for n in range(2, 11):
        llm.responses.append(f"Question {n}?")
        r = client.post(f"/interviews/{iid}/answers", json={"text": f"Answer {n - 1}"})
        assert r.status_code == 200, r.text
        assert r.json()["question_count"] == n
        assert r.json()["messages"][-1]["role"] == "question"

    llm.responses.append("Thanks for your time, the project story was a good example.")
    llm.responses.append(_judge_reply(10))  # background Judge runs right after the response
    r = client.post(f"/interviews/{iid}/answers", json={"text": "Answer 10"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "judging"
    assert body["question_count"] == 10
    assert body["messages"][-1]["role"] == "closing"
    assert body["ended_early"] is False

    closing_call, judge_call = llm.calls[-2], llm.calls[-1]
    assert "last question" in closing_call["messages"][-1]["content"]
    assert judge_call["json_schema"] is not None
    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"

    r = client.post(f"/interviews/{iid}/answers", json={"text": "one more"})
    assert r.status_code == 409


def test_next_question_prompt_carries_transcript_and_remaining_count(client, llm):
    iid = _start(client, llm)["id"]
    llm.responses.append("Follow-up?")
    client.post(f"/interviews/{iid}/answers", json={"text": "I led the migration."})
    msgs = llm.calls[-1]["messages"]
    assert msgs[1]["role"] == "assistant"
    assert msgs[2] == {"role": "user", "content": "I led the migration."}
    assert "9 question(s) remain" in msgs[-1]["content"]


def test_empty_answer_is_still_an_answer(client, llm):
    iid = _start(client, llm)["id"]
    llm.responses.append("Next?")
    r = client.post(f"/interviews/{iid}/answers", json={"text": ""})
    assert r.status_code == 200
    assert r.json()["messages"][1] == {"id": 2, "role": "answer", "text": "", "position": 1}
    assert llm.calls[-1]["messages"][2]["content"] == "(no answer given)"


def test_early_end_produces_closing_and_marks_ended_early(client, llm):
    iid = _start(client, llm)["id"]
    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    llm.responses.append("Understood, thanks for the migration story.")
    llm.responses.append(_judge_reply(1))
    r = client.post(f"/interviews/{iid}/end")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "judging"
    assert body["ended_early"] is True
    assert body["messages"][-1]["role"] == "closing"
    assert "end the interview early" in llm.calls[-2]["messages"][-1]["content"]


def test_early_end_requires_at_least_one_answer(client, llm):
    iid = _start(client, llm)["id"]
    r = client.post(f"/interviews/{iid}/end")
    assert r.status_code == 409
    assert llm.responses == []


def test_llm_failure_leaves_no_partial_answer(client, llm, db):
    iid = _start(client, llm)["id"]
    llm.responses.append(LLMUnavailable("rate limited"))
    r = client.post(f"/interviews/{iid}/answers", json={"text": "lost?"})
    assert r.status_code == 503
    assert "unavailable" in r.json()["detail"]

    db.expire_all()
    interview = db.get(Interview, iid)
    assert [m.role for m in interview.messages] == ["question"]
    assert db.query(Message).count() == 1
    assert interview.status == "in_progress"

    llm.responses.append("Q2 after retry?")
    r = client.post(f"/interviews/{iid}/answers", json={"text": "retry"})
    assert r.status_code == 200
    assert [m["role"] for m in r.json()["messages"]] == ["question", "answer", "question"]


def test_llm_failure_on_start_creates_nothing(client, llm, db):
    llm.responses += [PERSONA, LLMUnavailable("down")]
    r = client.post("/interviews", json={"title": "PM"})
    assert r.status_code == 503
    assert db.query(Interview).count() == 0


def test_get_unknown_interview_is_404(client):
    assert client.get("/interviews/999").status_code == 404
    assert client.post("/interviews/999/answers", json={"text": "x"}).status_code == 404


def test_resume_returns_full_transcript(client, llm):
    iid = _start(client, llm)["id"]
    llm.responses.append("Q2?")
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    r = client.get(f"/interviews/{iid}")
    assert r.status_code == 200
    assert [m["text"] for m in r.json()["messages"]][1:] == ["A1", "Q2?"]
