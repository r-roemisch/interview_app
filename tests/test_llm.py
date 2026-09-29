import httpx
import openai
import pytest

from interview_app.llm import FakeLLMClient, LLMUnavailable, OpenRouterClient


def _make_client(**kw) -> OpenRouterClient:
    return OpenRouterClient(api_key="test", model="test/model", sleep=lambda s: None, **kw)


def _connection_error() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=httpx.Request("POST", "http://x"))


def _rate_limit_error() -> openai.RateLimitError:
    resp = httpx.Response(429, request=httpx.Request("POST", "http://x"))
    return openai.RateLimitError("rate limited", response=resp, body=None)


class _Reply:
    def __init__(self, text: str | None):
        msg = type("Msg", (), {"content": text})()
        self.choices = [type("Choice", (), {"message": msg})()]


def test_retries_then_succeeds(monkeypatch):
    client = _make_client(max_retries=2)
    outcomes = [_connection_error(), _rate_limit_error(), _Reply("hello")]

    def fake_create(**kwargs):
        o = outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return o

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    assert client.complete([{"role": "user", "content": "hi"}]) == "hello"
    assert outcomes == []


def test_retry_exhaustion_raises_llm_unavailable(monkeypatch):
    client = _make_client(max_retries=2)
    attempts = []

    def fake_create(**kwargs):
        attempts.append(1)
        raise _connection_error()

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    with pytest.raises(LLMUnavailable):
        client.complete([{"role": "user", "content": "hi"}])
    assert len(attempts) == 3  # initial call + 2 retries


def test_non_retryable_error_becomes_unavailable_without_retry(monkeypatch):
    client = _make_client(max_retries=2)
    resp = httpx.Response(404, request=httpx.Request("POST", "http://x"))
    attempts = []

    def fake_create(**kwargs):
        attempts.append(1)
        raise openai.NotFoundError(
            # the SDK hands over the body with OpenRouter's outer "error" already unwrapped
            "blocked", response=resp, body={"message": "Model blocked by guardrail"}
        )

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    with pytest.raises(LLMUnavailable, match="test/model is not on your OpenRouter allow-list"):
        client.complete([{"role": "user", "content": "hi"}])
    assert len(attempts) == 1


def test_rejection_shows_the_providers_message(monkeypatch):
    client = _make_client()
    resp = httpx.Response(401, request=httpx.Request("POST", "http://x"))

    def fake_create(**kwargs):
        raise openai.AuthenticationError(
            "Error code: 401 - {...}", response=resp, body={"message": "No auth credentials found", "code": 401}
        )

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    with pytest.raises(LLMUnavailable, match="^No auth credentials found$"):
        client.complete([{"role": "user", "content": "hi"}])


def test_reply_without_choices_is_unavailable(monkeypatch):
    client = _make_client()
    reply = _Reply("unused")
    reply.choices = None  # OpenRouter's 200-with-error-body shape
    monkeypatch.setattr(client._client.chat.completions, "create", lambda **kw: reply)
    with pytest.raises(LLMUnavailable):
        client.complete([{"role": "user", "content": "hi"}])


def test_json_schema_is_passed_as_response_format(monkeypatch):
    client = _make_client()
    seen = {}

    def fake_create(**kwargs):
        seen.update(kwargs)
        return _Reply('{"a": 1}')

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
    assert client.complete([{"role": "user", "content": "x"}], json_schema=schema) == '{"a": 1}'
    assert seen["response_format"]["type"] == "json_schema"
    assert seen["response_format"]["json_schema"]["schema"] == schema
    assert seen["response_format"]["json_schema"]["strict"] is False  # see comment in llm.py
    assert seen["model"] == "test/model"


def test_empty_content_is_unavailable(monkeypatch):
    client = _make_client()
    monkeypatch.setattr(client._client.chat.completions, "create", lambda **kw: _Reply(None))
    with pytest.raises(LLMUnavailable):
        client.complete([{"role": "user", "content": "x"}])


def test_fake_returns_scripted_replies_and_records_calls():
    fake = FakeLLMClient(responses=["first", "second"])
    assert fake.complete([{"role": "user", "content": "a"}]) == "first"
    assert fake.complete([{"role": "user", "content": "b"}], json_schema={"type": "object"}) == "second"
    assert [c["messages"][0]["content"] for c in fake.calls] == ["a", "b"]
    assert fake.calls[1]["json_schema"] == {"type": "object"}


def test_fake_raises_scripted_exception_and_fails_when_exhausted():
    fake = FakeLLMClient(responses=[LLMUnavailable("down")])
    with pytest.raises(LLMUnavailable):
        fake.complete([])
    with pytest.raises(AssertionError):
        fake.complete([])


def test_dev_fake_answers_each_prompt_kind():
    import json

    from interview_app.llm import DevFakeLLMClient

    fake = DevFakeLLMClient()
    q1 = fake.complete([{"role": "system", "content": "You are a professional interviewer"}, {"role": "user", "content": "Please begin the interview."}])
    assert q1.startswith("Hello")
    q2 = fake.complete([{"role": "system", "content": "interviewer"}, {"role": "assistant", "content": q1}, {"role": "user", "content": "A1"}, {"role": "system", "content": "Ask the next question now."}])
    assert q2 != q1
    closing = fake.complete([{"role": "system", "content": "interviewer"}, {"role": "system", "content": "Write a brief, courteous closing message"}])
    assert "Thank you" in closing
    judge = json.loads(fake.complete([{"role": "system", "content": "You are an experienced hiring manager"}, {"role": "user", "content": "CANDIDATE (answer 1): x\n\nCANDIDATE (answer 2): y"}]))
    assert len(judge["answers"]) == 2 and judge["verdict"] == "hire"
    persona = json.loads(fake.complete([{"role": "system", "content": "You invent the interviewer"}, {"role": "user", "content": "Job: x"}]))
    assert persona == {"name": "Sam Taylor", "title": "Engineering Manager", "voice": "ash"}
    rec = json.loads(fake.complete([{"role": "system", "content": "You extract structured fields"}, {"role": "user", "content": "jd"}]))
    assert rec["seniority"] == "mid"
