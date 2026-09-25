# 02 LLM client with retries and fake

Status: ready-for-agent
Blocked by: 01

`llm.py`: a `LLMClient` protocol with `complete(messages, *, json_schema=None) -> str`. Real implementation uses the `openai` SDK with `base_url="https://openrouter.ai/api/v1"`, model from settings, 2 automatic retries on transport/rate-limit errors with short backoff, then raises `LLMUnavailable`. `FakeLLMClient` returns scripted responses in order for tests. Provide the client through a FastAPI dependency so tests can override it.

Done when unit tests cover: retry then success, retry exhaustion raises, fake returns scripted replies.
