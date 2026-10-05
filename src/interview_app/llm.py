"""LLM access. One thin wrapper so the provider can be swapped in one file (see spec)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol, TypeVar

import openai

from interview_app.config import get_settings

log = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GUARDRAILS_URL = "https://openrouter.ai/workspaces/default/guardrails"

T = TypeVar("T")

Message = dict[str, str]  # {"role": "system" | "user" | "assistant", "content": str}


def strip_code_fence(text: str) -> str:
    """Free models often wrap JSON in ```json fences even when told not to."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


class LLMUnavailable(Exception):
    """Raised when the model could not be reached after all automatic retries."""


class LLMClient(Protocol):
    def complete(
        self, messages: list[Message], *, json_schema: dict[str, Any] | None = None, model: str | None = None
    ) -> str:
        """Return the assistant's text for the given conversation.

        When `json_schema` is given the model is asked to produce JSON matching it.
        Callers must still validate the result: free models do not always comply.
        `model` overrides the client's own model for this call (the Interviewer Model).
        """
        ...


# Errors worth retrying: the request never reached the model or the provider hiccupped.
_RETRYABLE = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
)


def rejection_message(body: Any, model: str, fallback: str) -> str:
    """The provider's error message, or a short one naming the model when the allow-list blocks it."""
    body = body if isinstance(body, dict) else {}
    # JEV passes OpenRouter's raw {"error": {"message": ...}}; the openai SDK has already unwrapped it.
    err = body.get("error") if isinstance(body.get("error"), dict) else body
    message = err.get("message") if isinstance(err.get("message"), str) else fallback
    if "guardrail" in message:
        return f"{model} is not on your OpenRouter allow-list. Add it at {GUARDRAILS_URL}"
    return message


class OpenRouterClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = OPENROUTER_BASE_URL,
        max_retries: int = 2,
        backoff_seconds: float = 1.0,
        timeout_seconds: float = 60.0,
        sleep=time.sleep,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self._sleep = sleep
        # The SDK's own retries are disabled so the policy lives in one place.
        self._client = openai.OpenAI(
            api_key=api_key, base_url=base_url, max_retries=0, timeout=timeout_seconds
        )

    def complete(
        self, messages: list[Message], *, json_schema: dict[str, Any] | None = None, model: str | None = None
    ) -> str:
        model = model or self.model
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        if json_schema is not None:
            # strict=False: OpenAI's strict mode rejects schemas with optional fields or
            # min/max constraints, which our Pydantic models have. The reply is validated
            # with Pydantic anyway, so the schema is guidance for the model, not a guarantee.
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "output", "strict": False, "schema": json_schema},
            }

        response = call_with_retries(
            lambda: self._client.chat.completions.create(**kwargs),
            model=model,
            max_retries=self.max_retries,
            backoff_seconds=self.backoff_seconds,
            sleep=self._sleep,
        )
        # OpenRouter sometimes answers 200 with an error body and no `choices`.
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMUnavailable("model returned an empty message")
        return content


def call_with_retries(fn: Callable[[], T], *, model: str, max_retries: int, backoff_seconds: float, sleep) -> T:
    """The one retry policy for OpenRouter calls made with the openai SDK (chat, speech)."""
    attempts = max_retries + 1
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except _RETRYABLE as exc:
            if attempt == attempts:
                log.error("%s unavailable after %d attempts: %s", model, attempts, exc)
                raise LLMUnavailable(str(exc)) from exc
            log.warning("%s attempt %d/%d failed (%s), retrying", model, attempt, attempts, type(exc).__name__)
            sleep(backoff_seconds * attempt)
        except openai.APIStatusError as exc:
            # Bad key, blocked model, bad request: retrying will not help, but the caller
            # still gets one exception type to handle.
            log.error("%s request rejected (%s): %s", model, type(exc).__name__, exc)
            raise LLMUnavailable(rejection_message(exc.body, model, str(exc))) from exc
    raise AssertionError("unreachable")


@dataclass
class FakeLLMClient:
    """Test double. Returns scripted responses in order; an Exception in the script is raised."""

    responses: list[str | Exception] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)

    def complete(
        self, messages: list[Message], *, json_schema: dict[str, Any] | None = None, model: str | None = None
    ) -> str:
        self.calls.append({"messages": messages, "json_schema": json_schema, "model": model})
        if not self.responses:
            raise AssertionError("FakeLLMClient has no responses left")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


class DevFakeLLMClient:
    """Offline stand-in for local development: recognises which prompt it is given and answers
    plausibly. Lets the frontend be developed without an API key. Selected with LLM_PROVIDER=fake."""

    _questions = [
        "Hello, thanks for joining. Tell me about a project you are proud of and your role in it.",
        "Describe a time you disagreed with a teammate. How did you handle it?",
        "Tell me about a deadline you missed. What happened and what did you change afterwards?",
        "Give me an example of when you had to learn something quickly to get a job done.",
        "Describe a situation where requirements changed late. What did you do?",
        "Tell me about a time you received difficult feedback.",
        "When did you have to convince someone senior to change course?",
        "Describe a mistake you made in production and how you handled it.",
        "Tell me about a time you helped a struggling colleague.",
        "What is a decision you made with incomplete information, and how did it turn out?",
    ]

    def complete(
        self, messages: list[Message], *, json_schema: dict[str, Any] | None = None, model: str | None = None
    ) -> str:
        import json

        system = messages[0]["content"] if messages else ""
        last = messages[-1]["content"] if messages else ""
        if "hiring manager" in system:
            answers = sum(m["content"].count("<answer n=") for m in messages if m["role"] == "user")
            rating = {"rating": 3, "comment": "Some structure, but the outcome is not quantified."}
            return json.dumps(
                {
                    "answers": [{"situation": rating, "task": rating, "action": rating, "result": rating}] * answers,
                    "overall_score": 64,
                    "justification": "The candidate gives relevant examples with a clear situation and "
                    "actions, but results are rarely quantified and the personal contribution is sometimes "
                    "blurred with the team's. (Generated by the fake provider.)",
                    "verdict": "hire",
                    "improvement_points": [
                        "End every story with a measurable result.",
                        "Say 'I' when describing what you personally did.",
                        "Keep the situation to two sentences and spend the time on actions.",
                    ],
                }
            )
        if "use the interviewer for something other than the interview" in system:
            # Lets the off-topic reminder be tried offline: an Answer containing "off-topic test" is off-topic.
            return json.dumps({"off_topic": "off-topic test" in last.lower()})
        if "invent the interviewer" in system:
            return json.dumps({"name": "Sam Taylor", "title": "Engineering Manager", "voice": "ash"})
        if "extract structured fields" in system:
            return json.dumps({"title": "Software Engineer", "industry": "Software", "seniority": "mid"})
        if "list 5 to 7 topics" in last:
            return (
                "1. A project the candidate led: ownership.\n2. A disagreement: collaboration.\n"
                "3. A missed deadline: accountability.\n4. Learning fast: adaptability.\n"
                "5. A hard decision: judgment. (Plan from the fake provider.)"
            )
        if "closing message" in last:
            reply = "Thank you for your time today. I appreciated the detail in your project example. We will be in touch."
        else:
            asked = sum(1 for m in messages if m["role"] == "assistant")
            reply = self._questions[min(asked, len(self._questions) - 1)]
        # Chain-of-thought and Self-check prompts ask for tags around the hidden work.
        if "<assessment>" in system:
            return f"<assessment>The last answer lacked a measurable result. (Fake assessment.)</assessment>{reply}"
        if "<final>" in system:
            return f"<draft>{reply} And one more thing?</draft> Two questions; drop the second. <final>{reply}</final>"
        return reply


@lru_cache
def _default_client() -> LLMClient:
    settings = get_settings()
    if settings.llm_provider == "fake":
        log.warning("LLM_PROVIDER=fake: using the offline scripted model")
        return DevFakeLLMClient()
    return OpenRouterClient(api_key=settings.openrouter_api_key, model=settings.llm_model)


def get_llm_client() -> Iterator[LLMClient]:
    """FastAPI dependency. Tests override this with a FakeLLMClient."""
    yield _default_client()
