import json

from interview_app.models import Evaluation, Interview, Message

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "Kore"})


def _judge_reply(answers: int, score: int) -> str:
    r = {"rating": 3, "comment": "ok"}
    return json.dumps(
        {
            "answers": [{"situation": r, "task": r, "action": r, "result": r}] * answers,
            "overall_score": score,
            "justification": "Fine.",
            "verdict": "hire",
            "improvement_points": ["a", "b", "c"],
        }
    )


def _start(client, llm, title, **extra) -> int:
    llm.responses += [PERSONA, f"Hi. First question for {title}?"]
    r = client.post("/interviews", json={"title": title} | extra)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _complete(client, llm, iid: int, score: int) -> None:
    llm.responses += ["Q2?"]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    llm.responses += ["Bye.", _judge_reply(1, score)]
    assert client.post(f"/interviews/{iid}/end").status_code == 200


def test_history_lists_newest_first_with_status_and_score(client, llm):
    first = _start(client, llm, "Analyst")
    second = _start(client, llm, "Engineer")
    _complete(client, llm, second, score=81)
    third = _start(client, llm, "Designer")
    llm.responses += ["Q2?"]
    client.post(f"/interviews/{third}/answers", json={"text": "A1"})
    llm.responses += ["Bye.", "garbage", "garbage"]
    client.post(f"/interviews/{third}/end")

    rows = client.get("/interviews").json()
    assert [r["title"] for r in rows] == ["Designer", "Engineer", "Analyst"]
    assert [r["status"] for r in rows] == ["evaluation_missing", "completed", "in_progress"]
    assert [r["overall_score"] for r in rows] == [None, 81, None]
    assert rows[2]["id"] == first
    assert set(rows[0]) == {"id", "title", "created_at", "status", "judge", "overall_score"}


def test_delete_cascades_and_is_idempotent_on_missing(client, llm, db):
    iid = _start(client, llm, "Analyst")
    _complete(client, llm, iid, score=50)
    assert db.query(Message).count() == 4  # Q, A, Q, closing
    assert db.query(Evaluation).count() == 1

    assert client.delete(f"/interviews/{iid}").status_code == 204
    db.expire_all()
    assert db.query(Interview).count() == 0
    assert db.query(Message).count() == 0
    assert db.query(Evaluation).count() == 0
    assert client.delete(f"/interviews/{iid}").status_code == 404


def test_practice_again_copies_job_snapshot_and_difficulty(client, llm):
    iid = _start(
        client,
        llm,
        "Engineer",
        industry="fintech",
        seniority="senior",
        job_description="Build APIs.",
        difficulty="hard",
    )
    _complete(client, llm, iid, score=70)

    llm.responses += [PERSONA, "Hi again. Q1?"]
    r = client.post(f"/interviews/{iid}/practice-again")
    assert r.status_code == 201, r.text
    new = r.json()
    assert new["id"] != iid
    assert new["status"] == "in_progress"
    assert new["question_count"] == 1
    assert new["messages"] == [{"id": new["messages"][0]["id"], "role": "question", "text": "Hi again. Q1?", "position": 0}]
    for field in ("title", "industry", "seniority", "job_description", "difficulty"):
        assert new[field] == {"title": "Engineer", "industry": "fintech", "seniority": "senior",
                              "job_description": "Build APIs.", "difficulty": "hard"}[field]
    assert "Build APIs." in llm.calls[-1]["messages"][0]["content"]

    original = client.get(f"/interviews/{iid}").json()
    assert original["status"] == "completed"
    assert len(client.get("/interviews").json()) == 2


def test_times_are_sent_with_their_utc_offset(client, llm):
    # SQLite drops the time zone; without it browsers read the time as local.
    iid = _start(client, llm, "Analyst")
    assert client.get(f"/interviews/{iid}").json()["created_at"].endswith("Z")
    assert client.get("/interviews").json()[0]["created_at"].endswith("Z")
