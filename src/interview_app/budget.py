"""Guard 2: the Daily Budget (CONTEXT.md; spec: interviewer-experiments).

Today's spending is OpenRouter's count for the key (`usage_daily` on `/api/v1/key`), so it includes
everything spent with the key that day, also outside this app.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from interview_app.config import get_settings
from interview_app.llm import OPENROUTER_BASE_URL

log = logging.getLogger(__name__)


def read_daily_spend(
    api_key: str, *, base_url: str = OPENROUTER_BASE_URL, transport: httpx.BaseTransport | None = None
) -> float | None:
    """Dollars spent with the key today, or None when they cannot be read (then nothing is blocked)."""
    try:
        with httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=10.0, transport=transport) as http:
            response = http.get(f"{base_url}/key")
        response.raise_for_status()
        spend = response.json()["data"]["usage_daily"]
        if isinstance(spend, bool) or not isinstance(spend, int | float):
            raise TypeError(f"usage_daily is {spend!r}")
        return float(spend)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        log.warning("Could not read today's spending, not checking the Daily Budget: %s", exc)
        return None


@dataclass
class FakeDailySpend:
    """Test double: today's spending is whatever the test sets."""

    value: float | None = None

    def __call__(self) -> float | None:
        return self.value


def get_daily_spend() -> float | None:
    """FastAPI dependency. With the offline fake provider there is no key, so nothing is checked."""
    settings = get_settings()
    if settings.llm_provider == "fake":
        return None
    return read_daily_spend(settings.openrouter_api_key)
