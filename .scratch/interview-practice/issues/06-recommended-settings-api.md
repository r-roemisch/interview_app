# 06 Recommended Settings API

Status: resolved
Blocked by: 02

`POST /recommend-settings` with `{job_description}` → `{title, industry, seniority}` from one LLM call returning JSON validated with Pydantic. Seniority must be one of junior/mid/senior; if the model returns anything else, default to mid. 400 on empty description, 503 on `LLMUnavailable`.

Done when tests cover: happy path, invalid seniority normalized, empty input rejected.

## Comments

- 2026-09-25: Done. `prompts/recommend.py` (`RecommendedSettings` with tolerant seniority parsing: prefix match on junior/mid/senior, anything else → mid; blank industry → null), `services/recommend.py` (one call, one retry on unparsable output), `routers/recommend.py` (`POST /recommend-settings`: 400 empty, 502 unusable twice, 503 unavailable). 6 tests.
