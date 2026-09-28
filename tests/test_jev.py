import json

import httpx
import pytest

from interview_app.jev import DevFakeJevClient, OpenRouterJevClient, choice, score, yes_no
from interview_app.llm import LLMUnavailable

QUESTIONS = {
    "situation": score("How clear is the Situation?", ["Missing", "Vague", "Clear"]),
    "verdict": choice("Hiring decision", {"hire": "Would hire", "no_hire": "Would not hire"}),
    "quantified": yes_no("Results are quantified"),
}
ANSWERS = {
    "situation": {"type": "score", "score": 1.4, "confidence": 0.8},
    "verdict": {"type": "choice", "choice": "hire", "confidence": 0.7},
    "quantified": {"type": "noul", "noul": 0.3},
}


def _client(*responses: httpx.Response | Exception, seen: list | None = None) -> OpenRouterJevClient:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        nxt = queue.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt

    return OpenRouterJevClient(
        api_key="key", model="typesafe/jev-test", sleep=lambda s: None, transport=httpx.MockTransport(handler)
    )


def test_sends_wire_format_and_returns_answers():
    seen = []
    client = _client(httpx.Response(200, json={"answers": ANSWERS}), seen=seen)
    assert client.decide("the transcript", QUESTIONS) == ANSWERS

    request = seen[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/systemone"
    assert request.headers["Authorization"] == "Bearer key"
    body = json.loads(request.content)
    assert body == {"model": "typesafe/jev-test", "state": "the transcript", "questions": QUESTIONS}
    assert body["questions"]["situation"]["criteria"] == ["Missing", "Vague", "Clear"]
    assert body["questions"]["quantified"] == {"type": "noul", "instructions": "Results are quantified"}


def test_retries_connection_errors_rate_limits_and_overload():
    client = _client(
        httpx.ConnectError("down"),
        httpx.Response(429),
        httpx.Response(529),
        httpx.Response(200, json={"answers": ANSWERS}),
    )
    client.max_retries = 3
    assert client.decide("s", QUESTIONS) == ANSWERS


def test_gives_up_after_retries():
    seen = []
    client = _client(*[httpx.Response(503)] * 3, seen=seen)
    with pytest.raises(LLMUnavailable, match="503"):
        client.decide("s", QUESTIONS)
    assert len(seen) == 3  # initial call + 2 retries


def test_rejected_request_fails_at_once_with_the_providers_message():
    seen = []
    client = _client(httpx.Response(422, json={"error": {"message": "criteria must be a list"}}), seen=seen)
    with pytest.raises(LLMUnavailable, match="criteria must be a list"):
        client.decide("s", QUESTIONS)
    assert len(seen) == 1


def test_allow_list_rejection_names_the_model():
    body = {"error": {"message": "Model blocked by guardrail: 5 endpoints excluded"}}
    client = _client(httpx.Response(404, json=body))
    with pytest.raises(LLMUnavailable, match="typesafe/jev-test is not on your OpenRouter allow-list"):
        client.decide("s", QUESTIONS)


@pytest.mark.parametrize(
    "answers",
    [
        {k: v for k, v in ANSWERS.items() if k != "verdict"},  # missing
        ANSWERS | {"quantified": {"type": "score", "score": 1}},  # wrong type
    ],
)
def test_missing_or_mistyped_answer_is_a_failure(answers):
    client = _client(httpx.Response(200, json={"answers": answers}))
    with pytest.raises(LLMUnavailable, match="did not answer"):
        client.decide("s", QUESTIONS)


def test_dev_fake_answers_every_question_with_its_type():
    answers = DevFakeJevClient().decide("s", QUESTIONS)
    assert {k: a["type"] for k, a in answers.items()} == {k: q["type"] for k, q in QUESTIONS.items()}
    assert 0 <= answers["situation"]["score"] <= 2
    assert answers["verdict"]["choice"] in ("hire", "no_hire")
    assert 0 <= answers["quantified"]["noul"] <= 1
