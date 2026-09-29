"""Portraits of the Persona (CONTEXT.md): one image model call through OpenRouter with the openai SDK."""

from __future__ import annotations

import base64
import struct
import time
import zlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol

import openai

from interview_app.config import get_settings
from interview_app.llm import OPENROUTER_BASE_URL, LLMUnavailable, call_with_retries

# Image types a browser shows, by their first bytes. The model usually sends PNG, but may not.
_IMAGE_TYPES = {b"\x89PNG": "image/png", b"\xff\xd8\xff": "image/jpeg", b"RIFF": "image/webp"}


def image_type(data: bytes) -> str | None:
    """The media type of an image, or None if it is none of the types above."""
    return next((t for magic, t in _IMAGE_TYPES.items() if data.startswith(magic)), None)


class ImageClient(Protocol):
    def portrait(self, prompt: str) -> bytes:
        """An image (usually PNG) made from `prompt`. Raises LLMUnavailable, also when the reply holds none."""
        ...


class OpenRouterImageClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        timeout_seconds: float = 120.0,
        sleep=time.sleep,
    ) -> None:
        self.model = model
        self._retry = {"max_retries": max_retries, "backoff_seconds": backoff_seconds, "sleep": sleep}
        self._client = openai.OpenAI(
            api_key=api_key, base_url=OPENROUTER_BASE_URL, max_retries=0, timeout=timeout_seconds
        )

    def portrait(self, prompt: str) -> bytes:
        response = call_with_retries(
            lambda: self._client.chat.completions.create(
                model=self.model, modalities=["image", "text"], messages=[{"role": "user", "content": prompt}]
            ),
            model=self.model,
            **self._retry,
        )
        message = response.choices[0].message if response.choices else None
        # OpenRouter puts generated images next to the text, as data URLs; the SDK keeps them as dicts.
        for image in (getattr(message, "images", None) or []) if message else []:
            url = (image.get("image_url") or {}).get("url", "")
            if url.startswith("data:image/") and ";base64," in url:
                data = base64.b64decode(url.split(";base64,", 1)[1])
                if image_type(data):
                    return data
        # Without an image the model usually says why (e.g. a refusal); keep that for the log.
        reason = (message.content or "").strip()[:200] if message else ""
        raise LLMUnavailable(f"{self.model} returned no image: {reason!r}")


@dataclass
class FakeImageClient:
    """Test double: `image` for every call, after raising the scripted `errors` one by one."""

    image: bytes = b"\x89PNG fake portrait"
    errors: list[Exception] = field(default_factory=list)
    prompts: list[str] = field(default_factory=list)

    def portrait(self, prompt: str) -> bytes:
        self.prompts.append(prompt)
        if self.errors:
            raise self.errors.pop(0)
        return self.image


def placeholder_png(size: int = 256, rgb: tuple[int, int, int] = (199, 210, 254)) -> bytes:
    """A plain square PNG (indigo-200), built by hand so the dev fake needs no image library."""

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    row = b"\x00" + bytes(rgb) * size  # filter byte, then RGB pixels
    header = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b"")


class DevFakeImageClient:
    """Offline stand-in for LLM_PROVIDER=fake: a plain placeholder square after a short pause,
    so the loading state can be seen."""

    def portrait(self, prompt: str) -> bytes:
        time.sleep(2)
        return placeholder_png()


@lru_cache
def _default_image_client() -> ImageClient:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return DevFakeImageClient()
    return OpenRouterImageClient(settings.openrouter_api_key, settings.image_model)


def get_image_client() -> Iterator[ImageClient]:
    """FastAPI dependency. Tests override this with a FakeImageClient."""
    yield _default_image_client()
