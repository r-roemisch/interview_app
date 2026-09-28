import json

import httpx
import openai
import pytest

from interview_app.llm import LLMUnavailable
from interview_app.routers.speech import MAX_AUDIO_BYTES
from interview_app.speech import DevFakeSpeechClient, OpenRouterSpeechClient

PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "Kore"})


def _start(client, llm) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. First question?"]
    return client.post("/interviews", json={"title": "Backend Engineer", "voice_interview": True}).json()


def test_question_is_spoken_in_the_persona_voice(client, llm, speech):
    iv = _start(client, llm)
    question = iv["messages"][0]
    r = client.get(f"/interviews/{iv['id']}/messages/{question['id']}/speech")
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/mpeg"
    assert r.content == speech.audio
    assert speech.calls == [{"speak": "Hi, I'm Priya. First question?", "voice": "Kore"}]


def test_answers_and_other_interviews_messages_are_not_spoken(client, llm):
    iv = _start(client, llm)
    llm.responses.append("Second question?")
    answer = next(m for m in client.post(f"/interviews/{iv['id']}/answers", json={"text": "A1"}).json()["messages"] if m["role"] == "answer")
    assert client.get(f"/interviews/{iv['id']}/messages/{answer['id']}/speech").status_code == 404

    other = _start(client, llm)
    assert client.get(f"/interviews/{other['id']}/messages/{iv['messages'][0]['id']}/speech").status_code == 404


def test_speech_failure_is_503(client, llm, speech):
    iv = _start(client, llm)
    speech.error = LLMUnavailable("down")
    assert client.get(f"/interviews/{iv['id']}/messages/{iv['messages'][0]['id']}/speech").status_code == 503


@pytest.mark.parametrize(
    ("content_type", "filename"),
    [("audio/webm;codecs=opus", "answer.webm"), ("audio/mp4", "answer.m4a"), ("audio/ogg", "answer.ogg")],
)
def test_transcription_returns_text_and_names_the_format(client, speech, content_type, filename):
    r = client.post("/transcriptions", files={"file": ("blob", b"audio bytes", content_type)})
    assert r.status_code == 200, r.text
    assert r.json() == {"text": "I led the migration."}
    assert speech.calls[-1] == {"transcribe": filename, "content_type": content_type.split(";")[0], "size": 11}


def test_transcription_rejects_other_formats_and_large_files(client):
    r = client.post("/transcriptions", files={"file": ("a.txt", b"hello", "text/plain")})
    assert (r.status_code, r.json()["detail"]) == (422, "This audio format is not supported.")
    r = client.post("/transcriptions", files={"file": ("a.webm", b"0" * (MAX_AUDIO_BYTES + 1), "audio/webm")})
    assert (r.status_code, r.json()["detail"]) == (422, "The recording is larger than 25 MB.")


def test_transcription_failure_is_503(client, speech):
    speech.error = LLMUnavailable("down")
    r = client.post("/transcriptions", files={"file": ("a.webm", b"x", "audio/webm")})
    assert r.status_code == 503


def test_openrouter_client_calls_the_audio_endpoints_with_retries(monkeypatch):
    client = OpenRouterSpeechClient("key", tts_model="tts/model", stt_model="stt/model", sleep=lambda s: None)
    seen = {}
    failures = [openai.APIConnectionError(request=httpx.Request("POST", "http://x"))]

    def fake_speech(**kwargs):
        if failures:
            raise failures.pop()
        seen["speech"] = kwargs
        return type("R", (), {"content": b"mp3"})()

    def fake_transcription(**kwargs):
        seen["transcription"] = kwargs
        return type("R", (), {"text": "  hello  "})()

    monkeypatch.setattr(client._client.audio.speech, "create", fake_speech)
    monkeypatch.setattr(client._client.audio.transcriptions, "create", fake_transcription)
    assert client.speak("Hi", "Kore") == b"mp3"
    assert seen["speech"] == {"model": "tts/model", "voice": "Kore", "input": "Hi", "response_format": "mp3"}
    assert client.transcribe(b"abc", "answer.webm", "audio/webm") == "hello"
    assert seen["transcription"] == {"model": "stt/model", "file": ("answer.webm", b"abc", "audio/webm")}


def test_dev_fake_speaks_mp3_frames_and_transcribes_a_sentence():
    fake = DevFakeSpeechClient()
    assert fake.speak("Hi", "Kore")[:2] == b"\xff\xfb"
    assert fake.transcribe(b"", "answer.webm", "audio/webm").endswith("percent.")
