"""JEV access: TypeSafe's typed-decision model, called through OpenRouter (ADR-0003).

JEV writes no text. It gets a state and named typed questions and returns one typed answer per
question. Questions and answers stay in JEV's JSON wire format (plain dicts), e.g.
    {"type": "score", "score": 3.2, "legend": {...}, "probabilities": {...}, "confidence": 0.9}
    {"type": "choice", "choice": "hire", "probabilities": {...}, "confidence": 0.8}
    {"type": "noul", "noul": 0.95}          # probability of "yes"
Plain HTTP with httpx (already installed by the openai SDK) instead of TypeSafe's SDK.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import httpx

from interview_app.config import get_settings
from interview_app.llm import OPENROUTER_BASE_URL, LLMUnavailable, rejection_message

log = logging.getLogger(__name__)

Question = dict[str, Any]
Answer = dict[str, Any]


def score(instructions: str, levels: list[str]) -> Question:
    """Ordered levels, lowest first (2-10). The answer's `score` is a float from 0 to len(levels)-1."""
    return {"type": "score", "instructions": instructions, "criteria": levels}


def choice(instructions: str, options: dict[str, str]) -> Question:
    """Pick one label; `options` maps each label to its description."""
    return {"type": "choice", "instructions": instructions, "criteria": options}


def yes_no(instructions: str) -> Question:
    return {"type": "noul", "instructions": instructions}


class JevClient(Protocol):
    def decide(self, state: str, questions: dict[str, Question]) -> dict[str, Answer]:
        """One answer per question, keyed like `questions`. Raises LLMUnavailable on any failure."""
        ...


def _check_answers(questions: dict[str, Question], answers: Any) -> dict[str, Answer]:
    if not isinstance(answers, dict):
        raise LLMUnavailable("JEV returned no answers")
    for name, q in questions.items():
        a = answers.get(name)
        if not isinstance(a, dict) or a.get("type") != q["type"]:
            raise LLMUnavailable(f"JEV did not answer '{name}'")
    return answers


class OpenRouterJevClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        url: str = f"{OPENROUTER_BASE_URL}/systemone",
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        timeout_seconds: float = 60.0,
        sleep=time.sleep,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.model = model
        self.url = url
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._sleep = sleep
        self._http = httpx.Client(
            headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout_seconds, transport=transport
        )

    def decide(self, state: str, questions: dict[str, Question]) -> dict[str, Answer]:
        body = {"model": self.model, "state": state, "questions": questions}
        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self._http.post(self.url, json=body)
            except httpx.TransportError as exc:  # connection failed or timed out
                error = f"{type(exc).__name__}: {exc}"
            else:
                # 429 rate limit, 5xx and TypeSafe's 529 "overloaded" are worth retrying.
                if response.status_code == 429 or response.status_code >= 500:
                    error = f"HTTP {response.status_code}"
                elif response.is_error:
                    raise LLMUnavailable(rejection_message(_json(response), self.model, response.text))
                else:
                    return _check_answers(questions, _json(response).get("answers"))
            if attempt == attempts:
                log.error("JEV unavailable after %d attempts: %s", attempts, error)
                raise LLMUnavailable(error)
            log.warning("JEV attempt %d/%d failed (%s), retrying", attempt, attempts, error)
            self._sleep(self.backoff_seconds * attempt)
        raise AssertionError("unreachable")


def _json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


@dataclass
class FakeJevClient:
    """Test double. Returns scripted answer dicts in order; an Exception in the script is raised."""

    responses: list[dict[str, Answer] | Exception] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def decide(self, state: str, questions: dict[str, Question]) -> dict[str, Answer]:
        self.calls.append({"state": state, "questions": questions})
        if not self.responses:
            raise AssertionError("FakeJevClient has no responses left")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


class DevFakeJevClient:
    """Offline stand-in for LLM_PROVIDER=fake: a plausible answer for any question."""

    def decide(self, state: str, questions: dict[str, Question]) -> dict[str, Answer]:
        answers: dict[str, Answer] = {}
        for i, (name, q) in enumerate(questions.items()):
            if q["type"] == "score":
                top = len(q["criteria"]) - 1
                answers[name] = {"type": "score", "score": top * (0.5 + 0.1 * (i % 3)), "confidence": 0.9 - 0.15 * (i % 3)}
            elif q["type"] == "choice":
                labels = list(q["criteria"])
                answers[name] = {"type": "choice", "choice": labels[len(labels) // 2], "confidence": 0.7}
            elif name.endswith("_flagged"):
                answers[name] = {"type": "noul", "noul": 0.05}  # never flag an Answer in dev
            else:
                answers[name] = {"type": "noul", "noul": round(0.2 + 0.1 * (i % 8), 2)}
        return answers


@lru_cache
def _default_jev_client() -> JevClient:
    settings = get_settings()
    if settings.llm_provider == "fake":
        return DevFakeJevClient()
    return OpenRouterJevClient(api_key=settings.openrouter_api_key, model=settings.jev_model)


def get_jev_client() -> Iterator[JevClient]:
    """FastAPI dependency. Tests override this with a FakeJevClient."""
    yield _default_jev_client()
