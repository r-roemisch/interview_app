# 02 LLM client with retries and fake

Status: resolved
Blocked by: 01

`llm.py`: a `LLMClient` protocol with `complete(messages, *, json_schema=None) -> str`. Real implementation uses the `openai` SDK with `base_url="https://openrouter.ai/api/v1"`, model from settings, 2 automatic retries on transport/rate-limit errors with short backoff, then raises `LLMUnavailable`. `FakeLLMClient` returns scripted responses in order for tests. Provide the client through a FastAPI dependency so tests can override it.

Done when unit tests cover: retry then success, retry exhaustion raises, fake returns scripted replies.

## Comments

- 2026-09-25: Done. `llm.py` has `LLMClient` protocol, `OpenRouterClient` (openai SDK, SDK retries off, 2 own retries with backoff on connection/timeout/429/5xx, other HTTP errors become `LLMUnavailable` immediately), `FakeLLMClient`, and the `get_llm_client` dependency; `conftest.py` overrides it with the fake. 7 unit tests.
- 2026-09-25: Real call against OpenRouter authenticated fine but every free model returned 404 "Model blocked by guardrail" (account data-policy setting). Not a code issue; user must enable free/training-permitted endpoints in their OpenRouter privacy settings.
