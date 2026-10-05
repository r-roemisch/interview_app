"""Guard 2: the Daily Budget (spec: interviewer-experiments, issue 04)."""

import json

import httpx
import pytest

from interview_app.budget import read_daily_spend

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})
BODY = {"title": "Backend Engineer", "portrait": False}


def _start(client, llm) -> int:
    llm.responses += [PERSONA, "Hi, I'm Priya. Q1?"]
    r = client.post("/interviews", json=BODY)
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.mark.parametrize("spent", [2.0, 2.13])
def test_starting_is_refused_at_or_over_the_budget(client, llm, daily_spend, spent):
    daily_spend.value = spent
    r = client.post("/interviews", json=BODY)
    assert r.status_code == 429
    assert r.json()["detail"] == f"Today's budget of $2.00 is used up (${spent:.2f} spent). Try again tomorrow."
    assert llm.calls == []


def test_practice_again_is_refused_over_the_budget(client, llm, daily_spend):
    iid = _start(client, llm)
    daily_spend.value = 5.0
    calls = len(llm.calls)
    assert client.post(f"/interviews/{iid}/practice-again").status_code == 429
    assert len(llm.calls) == calls


@pytest.mark.parametrize("spent", [1.99, None])
def test_under_the_budget_or_unknown_spending_starts(client, llm, daily_spend, spent):
    daily_spend.value = spent
    _start(client, llm)


def test_a_running_interview_is_never_stopped_by_the_budget(client, llm, daily_spend):
    iid = _start(client, llm)
    daily_spend.value = 99.0
    llm.responses.append("Q2?")
    assert client.post(f"/interviews/{iid}/answers", json={"text": "A1"}).status_code == 200
    llm.responses.append("Bye.")
    assert client.post(f"/interviews/{iid}/end").status_code == 200


# --- reading the spending ---


def _read(response: httpx.Response | Exception) -> tuple[float | None, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if isinstance(response, Exception):
            raise response
        return response

    return read_daily_spend("key", transport=httpx.MockTransport(handler)), seen


def test_reads_usage_daily_from_the_key_endpoint():
    spend, seen = _read(httpx.Response(200, json={"data": {"usage": 9.1, "usage_daily": 0.42}}))
    assert spend == 0.42
    assert str(seen[0].url) == "https://openrouter.ai/api/v1/key"
    assert seen[0].headers["Authorization"] == "Bearer key"


@pytest.mark.parametrize(
    "response",
    [
        httpx.ConnectError("down"),
        httpx.Response(401, json={"error": {"message": "bad key"}}),
        httpx.Response(200, json={"data": {}}),
        httpx.Response(200, json={"data": {"usage_daily": "lots"}}),
        httpx.Response(200, text="not json"),
    ],
)
def test_unreadable_spending_is_none(response):
    assert _read(response)[0] is None
