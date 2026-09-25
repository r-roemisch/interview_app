# 06 Recommended Settings API

Status: ready-for-agent
Blocked by: 02

`POST /recommend-settings` with `{job_description}` → `{title, industry, seniority}` from one LLM call returning JSON validated with Pydantic. Seniority must be one of junior/mid/senior; if the model returns anything else, default to mid. 400 on empty description, 503 on `LLMUnavailable`.

Done when tests cover: happy path, invalid seniority normalized, empty input rejected.
