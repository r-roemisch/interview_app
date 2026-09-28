# 01 JEV client

Status: resolved
Blocked by: none

A thin client for JEV, next to the existing LLM client, so the JEV Judge can be built and tested against a fake. See spec "The JEV Judge" and "Config", and ADR-0003.

- Add `typesafe-sdk` with `uv add`. Point it at OpenRouter (`base_url="https://openrouter.ai/api"`) with the existing `OPENROUTER_API_KEY`. Check the SDK's actual response shape before relying on it: sources disagree between `response.answers[...]` and per-type collections.
- New module (e.g. `interview_app/jev.py`): a `JevClient` protocol with one method that takes a state and a dict of typed questions (score with level descriptions, choice with labelled criteria, noul/yes-no) and returns plain typed results (score float + confidence, choice label + confidence, yes probability). Keep SDK types out of the rest of the app.
- Retry policy as in `OpenRouterClient`: 2 retries with backoff for connection, timeout, rate-limit and server errors; rejected requests fail at once. All failures raise one exception type (reuse `LLMUnavailable` or add a sibling).
- Config: `JEV_MODEL`, default `typesafe/jev-1.13`, added to `config.py` and `.env.example`.
- `FakeJevClient` (scripted, for tests) and a dev fake used when `LLM_PROVIDER=fake` (plausible scores, confidences and probabilities for any questions it is given).
- When OpenRouter rejects a request because the model is not on the account's allow-list, the error message names the model and says to add it to the allow-list. Apply the same to `OpenRouterClient`, so the voice models get this later for free.
- README agent section: `JEV_MODEL`, and that `typesafe/jev-1.13` must be on the allow-list.

Done when tests cover: questions and results are translated both ways; retries happen for retryable errors and not for rejected ones; the allow-list rejection message names the model; the dev fake answers every question it is given.

## Comments

- 2026-09-29: Done without `typesafe-sdk` (it pulls in `httpx2` and `tenacity`; user: "do not bloat the app"). OpenRouter's `POST /api/v1/systemone` takes TypeSafe's wire format, so `jev.py` posts it with `httpx`, which the `openai` SDK already installs; `httpx` moved from dev to main dependencies because the app now imports it. Questions and answers stay in JEV's JSON wire format (plain dicts) with `score`/`choice`/`yes_no` helpers; `decide(state, questions)` checks every question got an answer of its type. Retries: transport errors, 429, 5xx (incl. 529); other errors fail at once. `llm.rejection_message` (shared with `OpenRouterClient`) turns OpenRouter's long guardrail message into "<model> is not on your OpenRouter allow-list. Add it at <url>". `JEV_MODEL` in config, `.env.example` and README. `FakeJevClient`, `DevFakeJevClient`, `get_jev_client` dependency. `tests/test_jev.py` 8 tests with `httpx.MockTransport`; 74 passed. A real call with the user's key worked: JEV is not blocked by the allow-list, so no README step is needed. Spec and ADR-0003 updated to say plain HTTP instead of the SDK.
