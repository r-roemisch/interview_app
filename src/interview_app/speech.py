"""Speech for Voice Interviews: the interviewer's voice and transcription of spoken Answers,
both through OpenRouter with the openai SDK (ADR-0004). No audio is ever stored."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import openai

from interview_app.config import get_settings
from interview_app.llm import OPENROUTER_BASE_URL, call_with_retries


class SpeechClient(Protocol):
    def speak(self, text: str, voice: str) -> bytes:
        """mp3 audio of `text` in `voice`. Raises LLMUnavailable."""
        ...

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        """The spoken text. `filename`'s extension tells the model the format. Raises LLMUnavailable."""
        ...


class OpenRouterSpeechClient:
    def __init__(
        self,
        api_key: str,
        *,
        tts_model: str,
        stt_model: str,
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        timeout_seconds: float = 60.0,
        sleep=time.sleep,
    ) -> None:
        self.tts_model = tts_model
        self.stt_model = stt_model
        self._retry = {"max_retries": max_retries, "backoff_seconds": backoff_seconds, "sleep": sleep}
        self._client = openai.OpenAI(
            api_key=api_key, base_url=OPENROUTER_BASE_URL, max_retries=0, timeout=timeout_seconds
        )

    def speak(self, text: str, voice: str) -> bytes:
        response = call_with_retries(
            lambda: self._client.audio.speech.create(model=self.tts_model, voice=voice, input=text, response_format="mp3"),
            model=self.tts_model,
            **self._retry,
        )
        return response.content

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        result = call_with_retries(
            lambda: self._client.audio.transcriptions.create(model=self.stt_model, file=(filename, audio, content_type)),
            model=self.stt_model,
            **self._retry,
        )
        return result.text.strip()


@dataclass
class FakeSpeechClient:
    """Test double: fixed audio and text, or `error` raised on every call."""

    audio: bytes = b"ID3 fake mp3"
    text: str = "I led the migration."
    error: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def speak(self, text: str, voice: str) -> bytes:
        self.calls.append({"speak": text, "voice": voice})
        if self.error:
            raise self.error
        return self.audio

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        self.calls.append({"transcribe": filename, "content_type": content_type, "size": len(audio)})
        if self.error:
            raise self.error
        return self.text


# Ten silent MPEG-1 Layer III frames (128 kbit/s, 44.1 kHz): about a quarter second of silence.
_SILENT_MP3 = (b"\xff\xfb\x90\x64" + b"\x00" * 413) * 10


class DevFakeSpeechClient:
    """Offline stand-in for LLM_PROVIDER=fake: silent speech and a fixed transcription."""

    def speak(self, text: str, voice: str) -> bytes:
        return _SILENT_MP3

    def transcribe(self, audio: bytes, filename: str, content_type: str) -> str:
        return "In my last role I led the move to a new billing system and cut costs by 20 percent."


@lru_cache
def _default_speech_client() -> SpeechClient:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return DevFakeSpeechClient()
    return OpenRouterSpeechClient(settings.openrouter_api_key, tts_model=settings.tts_model, stt_model=settings.stt_model)


def get_speech_client() -> Iterator[SpeechClient]:
    """FastAPI dependency. Tests override this with a FakeSpeechClient."""
    yield _default_speech_client()
