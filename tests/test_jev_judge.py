import json

from interview_app.llm import LLMUnavailable
from interview_app.prompts.jev_judge import CHECKLIST

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})
CV = "Led the billing migration at Acme."


def _jev_answers(answers: int, *, star=2.0, overall=4.5, verdict="hire", checks=None) -> dict:
    checks = checks or [0.9] * len(CHECKLIST)
    out = {}
    for n in range(1, answers + 1):
        for part in ("situation", "task", "action", "result"):
            out[f"answer{n}_{part}"] = {"type": "score", "score": star, "confidence": 0.8}
    out["overall"] = {"type": "score", "score": overall, "confidence": 0.7}
    out["verdict"] = {"type": "choice", "choice": verdict, "confidence": 0.6}
    for i, p in enumerate(checks):
        out[f"check{i}"] = {"type": "noul", "noul": p}
    return out


def _finished_interview(client, llm, *, answers=2, judge="jev", **overrides) -> int:
    """Start, answer, end early. The Closing triggers the chosen Judge in the background."""
    llm.responses += [PERSONA, "Hi, I'm Priya. First question?"]
    body = {"title": "Backend Engineer", "seniority": "senior", "judge": judge} | overrides
    iid = client.post("/interviews", json=body).json()["id"]
    for i in range(answers):
        llm.responses.append(f"Question {i + 2}?")
        client.post(f"/interviews/{iid}/answers", json={"text": f"Answer {i + 1}"})
    llm.responses.append("Thanks, bye.")
    assert client.post(f"/interviews/{iid}/end").status_code == 200
    return iid


def test_jev_request_has_star_overall_verdict_and_checklist_questions(client, llm, jev):
    jev.responses.append(_jev_answers(2))
    _finished_interview(client, llm, cv=CV, difficulty="hard")

    call = jev.calls[0]
    questions = call["questions"]
    assert len(questions) == 2 * 4 + 2 + len(CHECKLIST)
    assert questions["answer2_result"]["type"] == "score" and len(questions["answer2_result"]["criteria"]) == 5
    assert questions["overall"]["type"] == "score" and len(questions["overall"]["criteria"]) == 10
    assert set(questions["verdict"]["criteria"]) == {"strong_hire", "hire", "no_hire"}
    assert questions["check0"]["type"] == "noul"

    assert "CANDIDATE (answer 2): Answer 2" in call["state"] and "Backend Engineer" in call["state"]
    assert CV not in call["state"] and "Head of Engineering" not in call["state"]  # no CV, no Persona


def test_jev_answers_become_an_evaluation(client, llm, jev):
    checks = [0.9, 0.2, 0.8, 0.05, 0.7, 0.3, 0.95, 0.6]
    jev.responses.append(_jev_answers(2, star=3.47, overall=4.5, verdict="strong_hire", checks=checks))
    iid = _finished_interview(client, llm)

    ev = client.get(f"/interviews/{iid}/evaluation").json()
    assert ev["judge"] == "jev"
    assert ev["overall_score"] == 50  # 4.5 of 9 levels
    assert ev["overall_confidence"] == 0.7
    assert (ev["verdict"], ev["verdict_confidence"]) == ("strong_hire", 0.6)
    assert ev["justification"] is None

    situation = ev["star_breakdowns"][1]["situation"]
    assert situation == {"rating": 4, "comment": None, "confidence": 0.8}  # round(3.47) + 1

    # The three checks JEV was least sure of, weakest first.
    assert ev["improvement_points"] == [CHECKLIST[3][1], CHECKLIST[1][1], CHECKLIST[5][1]]
    assert [c["probability"] for c in ev["checklist"]] == checks

    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"
    row = client.get("/interviews").json()[0]
    assert (row["judge"], row["overall_score"]) == ("jev", 50)


def test_star_ratings_and_overall_score_stay_in_range(client, llm, jev):
    jev.responses.append(_jev_answers(1, star=-0.4, overall=9.6))
    iid = _finished_interview(client, llm, answers=1)
    ev = client.get(f"/interviews/{iid}/evaluation").json()
    assert ev["star_breakdowns"][0]["task"]["rating"] == 1
    assert ev["overall_score"] == 100


def test_jev_failure_marks_evaluation_missing_and_rerun_uses_jev_again(client, llm, jev):
    jev.responses.append(LLMUnavailable("down"))
    iid = _finished_interview(client, llm)
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"
    assert client.get(f"/interviews/{iid}/evaluation").status_code == 409

    jev.responses.append(_jev_answers(2))
    assert client.post(f"/interviews/{iid}/evaluation/rerun").status_code == 202
    assert client.get(f"/interviews/{iid}/evaluation").json()["judge"] == "jev"
    assert len(jev.calls) == 2
    assert not any("hiring manager" in c["messages"][0]["content"] for c in llm.calls)  # no LLM Judge


def test_unusable_jev_answer_marks_evaluation_missing(client, llm, jev):
    jev.responses.append(_jev_answers(2, verdict="maybe"))
    iid = _finished_interview(client, llm)
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"


def test_rerun_on_completed_keeps_one_evaluation(client, llm, jev, db):
    from interview_app.models import Evaluation

    jev.responses += [_jev_answers(2, overall=0), _jev_answers(2, overall=9)]
    iid = _finished_interview(client, llm)
    client.post(f"/interviews/{iid}/evaluation/rerun")
    assert client.get(f"/interviews/{iid}/evaluation").json()["overall_score"] == 100
    assert db.query(Evaluation).filter_by(interview_id=iid).count() == 1


def test_judge_is_stored_returned_and_copied_by_practice_again(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iid = _finished_interview(client, llm, answers=1)
    assert client.get(f"/interviews/{iid}").json()["judge"] == "jev"

    llm.responses += [PERSONA, "Hello again. First question?"]
    again = client.post(f"/interviews/{iid}/practice-again").json()
    assert again["judge"] == "jev"


def test_llm_judge_is_the_default_and_stores_no_confidences(client, llm, jev):
    r = {"rating": 3, "comment": "ok"}
    judge_reply = {
        "answers": [{"situation": r, "task": r, "action": r, "result": r}],
        "overall_score": 60,
        "justification": "Fine.",
        "verdict": "hire",
        "improvement_points": ["a", "b", "c"],
    }
    llm.responses += [PERSONA, "First question?", "Thanks, bye.", json.dumps(judge_reply)]
    iid = client.post("/interviews", json={"title": "Backend Engineer"}).json()["id"]
    client.post(f"/interviews/{iid}/answers", json={"text": "A1"})
    llm.responses.insert(0, "Question 2?")  # the answer above needs a next Question first
    client.post(f"/interviews/{iid}/end")

    ev = client.get(f"/interviews/{iid}/evaluation").json()
    assert ev["judge"] == "llm"
    assert ev["overall_confidence"] is None and ev["checklist"] is None
    assert ev["star_breakdowns"][0]["situation"] == {"rating": 3, "comment": "ok", "confidence": None}
    assert jev.calls == []


def _llm_judge_reply(answers: int, score: int = 60) -> str:
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


def test_other_judge_adds_a_second_evaluation_without_touching_status(client, llm, jev):
    jev.responses.append(_jev_answers(2, overall=4.5))
    iid = _finished_interview(client, llm)

    llm.responses.append(_llm_judge_reply(2, score=80))
    r = client.post(f"/interviews/{iid}/evaluations/llm")
    assert r.status_code == 201, r.text
    assert (r.json()["judge"], r.json()["overall_score"]) == ("llm", 80)

    both = client.get(f"/interviews/{iid}/evaluations").json()
    assert sorted(e["judge"] for e in both) == ["jev", "llm"]
    assert client.get(f"/interviews/{iid}/evaluation").json()["judge"] == "jev"  # still the chosen one
    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"
    assert client.get("/interviews").json()[0]["overall_score"] == 50


def test_running_the_other_judge_twice_keeps_one_evaluation_per_judge(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iid = _finished_interview(client, llm, answers=1)
    llm.responses += [_llm_judge_reply(1, score=30), _llm_judge_reply(1, score=90)]
    client.post(f"/interviews/{iid}/evaluations/llm")
    client.post(f"/interviews/{iid}/evaluations/llm")

    both = client.get(f"/interviews/{iid}/evaluations").json()
    assert len(both) == 2
    assert next(e for e in both if e["judge"] == "llm")["overall_score"] == 90


def test_other_judge_is_409_for_the_chosen_judge_and_while_in_progress(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iid = _finished_interview(client, llm, answers=1)
    assert client.post(f"/interviews/{iid}/evaluations/jev").status_code == 409

    llm.responses += [PERSONA, "First question?"]
    open_iid = client.post("/interviews", json={"title": "PM", "judge": "jev"}).json()["id"]
    assert client.post(f"/interviews/{open_iid}/evaluations/llm").status_code == 409


def test_other_judge_failure_is_503_and_changes_nothing(client, llm, jev):
    jev.responses.append(_jev_answers(1))
    iid = _finished_interview(client, llm, answers=1)
    llm.responses.append(LLMUnavailable("down"))

    r = client.post(f"/interviews/{iid}/evaluations/llm")
    assert r.status_code == 503
    assert [e["judge"] for e in client.get(f"/interviews/{iid}/evaluations").json()] == ["jev"]
    assert client.get(f"/interviews/{iid}").json()["status"] == "completed"


def test_other_judge_runs_even_when_the_chosen_one_is_missing(client, llm, jev):
    """The chosen JEV Judge failed; the LLM Judge can still be compared, and the status stays."""
    jev.responses.append(LLMUnavailable("down"))
    iid = _finished_interview(client, llm, answers=1)
    llm.responses.append(_llm_judge_reply(1))
    assert client.post(f"/interviews/{iid}/evaluations/llm").status_code == 201
    assert client.get(f"/interviews/{iid}").json()["status"] == "evaluation_missing"
