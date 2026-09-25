from interview_app.models import (
    Difficulty,
    Evaluation,
    Interview,
    InterviewStatus,
    Message,
    MessageRole,
    Seniority,
    Verdict,
)
from interview_app.schemas import EvaluationOut, InterviewOut


def _breakdown(position: int) -> dict:
    r = {"rating": 4, "comment": "fine"}
    return {"position": position, "situation": r, "task": r, "action": r, "result": r}


def test_interview_with_messages_and_evaluation_round_trips(db):
    interview = Interview(title="Backend Engineer", seniority=Seniority.SENIOR, difficulty=Difficulty.HARD)
    interview.messages = [
        Message(role=MessageRole.QUESTION, text="Hi. Tell me about a conflict.", position=0),
        Message(role=MessageRole.ANSWER, text="Once upon a time...", position=1),
        Message(role=MessageRole.CLOSING, text="Thanks, that's all.", position=2),
    ]
    interview.status = InterviewStatus.COMPLETED
    interview.evaluation = Evaluation(
        overall_score=72,
        justification="Solid but thin on results.",
        verdict=Verdict.HIRE,
        improvement_points=["Quantify outcomes", "Name your own role", "Shorter setup"],
        star_breakdowns=[_breakdown(1)],
    )
    db.add(interview)
    db.commit()
    db.expunge_all()

    loaded = db.get(Interview, interview.id)
    assert loaded is not None
    assert loaded.title == "Backend Engineer"
    assert loaded.seniority == Seniority.SENIOR
    assert loaded.status == InterviewStatus.COMPLETED
    assert [m.role for m in loaded.messages] == [
        MessageRole.QUESTION,
        MessageRole.ANSWER,
        MessageRole.CLOSING,
    ]
    assert loaded.question_count == 1
    assert loaded.answer_count == 1
    assert loaded.evaluation is not None
    assert loaded.evaluation.verdict == Verdict.HIRE
    assert loaded.evaluation.star_breakdowns[0]["situation"]["rating"] == 4

    out = InterviewOut.model_validate(loaded)
    assert out.question_cap == 10
    assert out.messages[2].role == MessageRole.CLOSING

    ev = EvaluationOut.model_validate(loaded.evaluation)
    assert ev.overall_score == 72
    assert ev.star_breakdowns[0].action.rating == 4
    assert len(ev.improvement_points) == 3


def test_defaults_are_mid_normal_in_progress(db):
    interview = Interview(title="Analyst")
    db.add(interview)
    db.commit()
    db.refresh(interview)
    assert interview.seniority == Seniority.MID
    assert interview.difficulty == Difficulty.NORMAL
    assert interview.status == InterviewStatus.IN_PROGRESS
    assert interview.ended_early is False
    assert interview.created_at is not None


def test_deleting_interview_cascades(db):
    interview = Interview(title="PM")
    interview.messages = [Message(role=MessageRole.QUESTION, text="Q", position=0)]
    interview.evaluation = Evaluation(
        overall_score=10, justification="x", verdict=Verdict.NO_HIRE, improvement_points=[], star_breakdowns=[]
    )
    db.add(interview)
    db.commit()

    db.delete(interview)
    db.commit()
    assert db.query(Message).count() == 0
    assert db.query(Evaluation).count() == 0
