import json

from fastapi.testclient import TestClient

from interview_app import db as db_module
from interview_app.llm import LLMUnavailable
from interview_app.main import create_app
from interview_app.models import Evaluation, Interview, InterviewStatus

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _rating(n=4, c="ok"):
    return {"rating": n, "comment": c}


def _assessment(n=4):
    return {"situation": _rating(n), "task": _rating(n), "action": _rating(n), "result": _rating(n)}


def _judge_json(answers: int, verdict="hire", score=70, points=None) -> str:
    return json.dumps(
        {
            "answers": [_assessment() for _ in range(answers)],
            "overall_score": score,
            "justification": "Reasonable structure, thin on results.",
            "verdict": verdict,
            "improvement_points": points or ["Quantify", "Own your role", "Be concise"],
        }
    )


def _finish_early(client, llm, answers=2) -> int:
    """Start an Interview, give `answers` Answers, end early. Caller scripts the Judge reply first."""
    llm.responses[:0] = [PERSONA, "Hi. Q1?"]
    iid = client.post("/interviews", json={"title": "Data Analyst"}).json()["id"]
    # each Answer is followed by a scripted next Question
    for n in range(answers):
        llm.responses.insert(0, f"Q{n + 2}?")
        assert client.post(f"/interviews/{iid}/answers", json={"text": f"A{n + 1}"}).status_code == 200
    llm.responses.insert(0, "Thanks, bye.")
    r = client.post(f"/interviews/{iid}/end")
    assert r.status_code == 200, r.text
    return iid


def test_valid_judge_output_completes_interview(client, llm, db):
    llm.responses.append(_judge_json(2, verdict="Strong Hire", score=88))
    iid = _finish_early(client, llm, answers=2)

    r = client.get(f"/interviews/{iid}")
    assert r.json()["status"] == "completed"

    r = client.get(f"/interviews/{iid}/evaluation")
    assert r.status_code == 200, r.text
    ev = r.json()
    assert ev["overall_score"] == 88
    assert ev["verdict"] == "strong_hire"
    assert len(ev["improvement_points"]) == 3
    assert [b["position"] for b in ev["star_breakdowns"]] == [1, 3]
    assert ev["star_breakdowns"][0]["situation"]["rating"] == 4

    judge_call = llm.calls[-1]
    assert judge_call["json_schema"]["title"] == "JudgeOutput"
    user = judge_call["messages"][1]["content"]
    assert "Data Analyst" in user
    assert "CANDIDATE (answer 2): A2" in user
    assert "`answers` must have 2 entries" in user


def test_invalid_then_valid_output_completes_after_one_retry(client, llm):
    llm.responses.append("Sure! Here is my evaluation: {not json")
    llm.responses.append("```json\n" + _judge_json(1) + "\n```")
    iid = _finish_early(client, llm, answers=1)

    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"
    retry_msgs = llm.calls[-1]["messages"]
    assert "previous output was rejected" in retry_msgs[-1]["content"]
    assert "not valid JSON" in retry_msgs[-1]["content"]


def test_wrong_answer_count_is_invalid(client, llm):
    llm.responses.append(_judge_json(3))  # interview has 1 answer
    llm.responses.append(_judge_json(1))
    iid = _finish_early(client, llm, answers=1)
    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"
    assert "expected 1" in llm.calls[-1]["messages"][-1]["content"]


def test_twice_invalid_marks_evaluation_missing(client, llm, db):
    llm.responses.append("nope")
    llm.responses.append(_judge_json(1, points=["only", "two"]))
    iid = _finish_early(client, llm, answers=1)

    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"
    r = client.get(f"/interviews/{iid}/evaluation")
    assert r.status_code == 409
    assert db.query(Evaluation).count() == 0


def test_llm_unavailable_marks_evaluation_missing_without_retry(client, llm):
    llm.responses.append(LLMUnavailable("down"))
    iid = _finish_early(client, llm, answers=1)
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"
    assert llm.responses == []


def test_rerun_from_evaluation_missing_succeeds(client, llm):
    llm.responses.append("nope")
    llm.responses.append("still nope")
    iid = _finish_early(client, llm, answers=1)
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"

    llm.responses.append(_judge_json(1, score=55))
    r = client.post(f"/interviews/{iid}/evaluation/rerun")
    assert r.status_code == 202
    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"
    assert client.get(f"/interviews/{iid}/evaluation").json()["overall_score"] == 55


def test_rerun_on_completed_replaces_evaluation(client, llm, db):
    llm.responses.append(_judge_json(1, score=40))
    iid = _finish_early(client, llm, answers=1)
    llm.responses.append(_judge_json(1, score=90))
    assert client.post(f"/interviews/{iid}/evaluation/rerun").status_code == 202
    assert client.get(f"/interviews/{iid}/evaluation").json()["overall_score"] == 90
    assert db.query(Evaluation).count() == 1


def test_evaluation_is_404_while_in_progress_and_rerun_is_409(client, llm):
    llm.responses += [PERSONA, "Hi. Q1?"]
    iid = client.post("/interviews", json={"title": "PM"}).json()["id"]
    assert client.get(f"/interviews/{iid}/evaluation").status_code == 404
    assert client.post(f"/interviews/{iid}/evaluation/rerun").status_code == 409


def test_rerun_is_409_while_the_judge_is_running(client, llm, db):
    llm.responses.append(_judge_json(1))
    iid = _finish_early(client, llm, answers=1)
    db.get(Interview, iid).status = InterviewStatus.JUDGING
    db.commit()
    r = client.post(f"/interviews/{iid}/evaluation/rerun")
    assert r.status_code == 409
    assert r.json()["detail"] == "The Judge is still running"


def test_startup_turns_interrupted_judging_into_evaluation_missing(engine, db, monkeypatch):
    # A server restart loses the background Judge; without this the Interview stays Judging forever.
    judging = Interview(title="PM", status=InterviewStatus.JUDGING)
    in_progress = Interview(title="QA")
    db.add_all([judging, in_progress])
    db.commit()

    monkeypatch.setattr(db_module, "engine", engine)
    with TestClient(create_app()):
        pass

    db.expire_all()
    assert db.get(Interview, judging.id).status == InterviewStatus.EVALUATION_MISSING
    assert db.get(Interview, in_progress.id).status == InterviewStatus.IN_PROGRESS
