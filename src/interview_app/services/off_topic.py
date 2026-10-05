"""Guard 1: is an Answer an Off-topic Answer? (CONTEXT.md; spec: interviewer-experiments)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Protocol

from interview_app.config import get_settings
from interview_app.llm import LLMClient, LLMUnavailable, _default_client, strip_code_fence
from interview_app.prompts.off_topic import messages_for_off_topic, off_topic_schema

log = logging.getLogger(__name__)


class OffTopicCheck(Protocol):
    def __call__(self, question: str, answer: str) -> bool: ...


@dataclass
class LLMOffTopicCheck:
    """One call to the off-topic model. Any failure counts as on-topic: the guard never blocks an Interview."""

    llm: LLMClient
    model: str

    def __call__(self, question: str, answer: str) -> bool:
        try:
            raw = self.llm.complete(
                messages_for_off_topic(question, answer), json_schema=off_topic_schema(), model=self.model
            )
            verdict = json.loads(strip_code_fence(raw))["off_topic"]
        except (LLMUnavailable, json.JSONDecodeError, KeyError, TypeError) as exc:
            log.warning("Off-topic check failed, counting the answer as on-topic: %s", exc)
            return False
        if not isinstance(verdict, bool):
            log.warning("Off-topic check gave %r, counting the answer as on-topic", verdict)
            return False
        return verdict


@dataclass
class FakeOffTopicCheck:
    """Test double: answers on-topic unless the Answer is in `off_topic`; records every call."""

    off_topic: set[str] = field(default_factory=set)
    calls: list[tuple[str, str]] = field(default_factory=list)

    def __call__(self, question: str, answer: str) -> bool:
        self.calls.append((question, answer))
        return answer in self.off_topic


def get_off_topic_check() -> OffTopicCheck:
    """FastAPI dependency. Tests override this with a FakeOffTopicCheck."""
    return LLMOffTopicCheck(_default_client(), get_settings().off_topic_model)
