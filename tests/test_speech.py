import base64
import json
import wave
from io import BytesIO
from types import SimpleNamespace

import httpx
import openai
import pytest

from interview_app.llm import LLMUnavailable
from interview_app.routers.speech import MAX_AUDIO_BYTES
from interview_app.speech import SAMPLE_RATE, DevFakeSpeechClient, OpenRouterSpeechClient

# The first bytes the transcription endpoint checks for (spec: security-guards C3).
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 20
MP3 = b"ID3\x04\x00" + b"\x00" * 20
PERSONA = json.dumps({"name": "Priya Nair", "title": "Head of Engineering", "voice": "coral"})


def _start(client, llm) -> dict:
    llm.responses += [PERSONA, "Hi, I'm Priya. First question?"]
    return client.post("/interviews", json={"title": "Backend Engineer", "voice_interview": True}).json()


def test_question_is_spoken_in_the_persona_voice(client, llm, speech):
    iv = _start(client, llm)
    question = iv["messages"][0]
    r = client.get(f"/interviews/{iv['id']}/messages/{question['id']}/speech")
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content == speech.audio
    assert speech.calls == [{"speak": "Hi, I'm Priya. First question?", "voice": "coral"}]


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


def test_written_interviews_are_never_spoken(client, llm, speech):
    llm.responses += [PERSONA, "Hi, I'm Priya. First question?"]
    iv = client.post("/interviews", json={"title": "Backend Engineer"}).json()
    assert client.get(f"/interviews/{iv['id']}/messages/{iv['messages'][0]['id']}/speech").status_code == 404
    assert speech.calls == []


@pytest.mark.parametrize(
    ("content_type", "audio", "audio_format"),
    [
        ("audio/wav", WAV, "wav"),
        ("audio/x-wav", WAV, "wav"),
        ("audio/mpeg", MP3, "mp3"),
        ("audio/mpeg", b"\xff\xfb\x90\x00" + b"\x00" * 20, "mp3"),  # an MPEG frame without an ID3 tag
    ],
)
def test_transcription_returns_text_and_names_the_format(client, speech, content_type, audio, audio_format):
    r = client.post("/transcriptions", files={"file": ("blob", audio, content_type)})
    assert r.status_code == 200, r.text
    assert r.json() == {"text": "I led the migration."}
    assert speech.calls[-1] == {"transcribe": audio_format, "size": len(audio)}


@pytest.mark.parametrize(
    ("content_type", "audio"),
    [("audio/wav", b"audio bytes that are not a wav"), ("audio/wav", MP3), ("audio/mpeg", WAV)],
)
def test_transcription_rejects_files_whose_bytes_do_not_match_their_type(client, speech, content_type, audio):
    r = client.post("/transcriptions", files={"file": ("blob", audio, content_type)})
    assert (r.status_code, r.json()["detail"]) == (422, "This audio format is not supported.")
    assert speech.calls == []


def test_transcription_rejects_other_formats_and_large_files(client):
    # The model cannot read the browser's own recording formats; the frontend sends WAV.
    for content_type in ("text/plain", "audio/webm;codecs=opus"):
        r = client.post("/transcriptions", files={"file": ("a", b"hello", content_type)})
        assert (r.status_code, r.json()["detail"]) == (422, "This audio format is not supported.")
    r = client.post("/transcriptions", files={"file": ("a.wav", b"0" * (MAX_AUDIO_BYTES + 1), "audio/wav")})
    assert (r.status_code, r.json()["detail"]) == (422, "The recording is larger than 25 MB.")


def test_transcription_failure_is_503(client, speech):
    speech.error = LLMUnavailable("down")
    r = client.post("/transcriptions", files={"file": ("a.wav", WAV, "audio/wav")})
    assert r.status_code == 503


def _client() -> OpenRouterSpeechClient:
    return OpenRouterSpeechClient("key", tts_model="tts/model", stt_model="stt/model", sleep=lambda s: None)


def _chunks(pcm: bytes, transcript: str) -> list:
    """A streamed audio reply as the SDK yields it: `audio` is a plain dict on the delta."""
    half = len(pcm) // 2
    parts = [(pcm[:half], transcript[:5]), (pcm[half:], transcript[5:])]
    chunks = [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(audio={"data": base64.b64encode(d).decode(), "transcript": t}))])
        for d, t in parts
    ]
    return [*chunks, SimpleNamespace(choices=[])]  # the last chunk carries only usage


def test_speak_streams_pcm_from_the_audio_model_and_returns_wav(monkeypatch):
    client = _client()
    calls = []
    failures = [openai.APIConnectionError(request=httpx.Request("POST", "http://x"))]

    def fake_create(**kwargs):
        calls.append(kwargs)
        if failures:
            raise failures.pop()
        return iter(_chunks(b"\x01\x00" * 100, "Why do you want this job?"))

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    audio = client.speak("Why do you want this job?", "coral")

    with wave.open(BytesIO(audio)) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()) == (1, 2, SAMPLE_RATE, 100)
    assert len(calls) == 2  # a connection error is retried
    kwargs = calls[-1]
    assert (kwargs["model"], kwargs["stream"], kwargs["modalities"]) == ("tts/model", True, ["text", "audio"])
    assert kwargs["audio"] == {"voice": "coral", "format": "pcm16"}
    assert kwargs["messages"][-1] == {"role": "user", "content": 'Say exactly: "Why do you want this job?"'}


def test_speak_refuses_a_reply_that_answers_instead_of_reading(monkeypatch):
    client = _client()
    replies = [_chunks(b"\x00\x00", "Well, I have always loved building products."), _chunks(b"\x00\x00", "Sure. Why do you want this job?")]
    monkeypatch.setattr(client._client.chat.completions, "create", lambda **kw: iter(replies.pop(0)))
    assert client.speak("Why do you want this job?", "coral")[:4] == b"RIFF"  # second try is close enough

    replies = [_chunks(b"\x00\x00", "I would love to."), _chunks(b"\x00\x00", "Great question!")]
    with pytest.raises(LLMUnavailable, match="did not read the text"):
        client.speak("Why do you want this job?", "coral")


def test_transcribe_sends_the_recording_to_the_audio_model(monkeypatch):
    client = _client()
    seen = {}

    def fake_create(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="  I led the migration.  "))])

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)
    assert client.transcribe(b"abc", "wav") == "I led the migration."
    assert seen["model"] == "stt/model"
    text, recording = seen["messages"][-1]["content"]
    assert text["type"] == "text"  # the instruction comes before the audio
    assert recording == {"type": "input_audio", "input_audio": {"data": base64.b64encode(b"abc").decode(), "format": "wav"}}


def test_transcribe_turns_the_silence_marker_into_an_empty_answer(monkeypatch):
    client = _client()
    reply = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="[silence]"))])
    monkeypatch.setattr(client._client.chat.completions, "create", lambda **kw: reply)
    assert client.transcribe(b"abc", "wav") == ""


def test_dev_fake_speaks_silent_wav_and_transcribes_a_sentence():
    fake = DevFakeSpeechClient()
    with wave.open(BytesIO(fake.speak("Hi", "coral"))) as w:
        assert w.getframerate() == SAMPLE_RATE and w.getnframes() > 0
    assert fake.transcribe(b"", "wav").endswith("percent.")
