# 15 Persona backend

Status: resolved
Blocked by: none

Give every Interview a Persona (see `CONTEXT.md` and spec "Persona").

- `models.py`: `persona_name`, `persona_title` on `Interview`.
- New prompt in `prompts/` asking for `{name, title}` as JSON, fitted to the Job snapshot. Validate with Pydantic.
- `start_interview`: call it before the first Question. On failure after retries, use "Alex Morgan, Hiring Manager" and continue.
- Interviewer prompts (Questions and Closing) are told the Persona's name and title only; no style instructions. Difficulty still controls tone.
- "Practice again" creates a fresh Persona (does not copy it).
- `InterviewOut` exposes the Persona. `HistoryRow` does not.
- Fake LLM returns a fixed Persona.
- The Judge prompt does not receive the Persona.
- `create_all` does not add columns: delete the local SQLite file once and add a README note saying so.

Done when tests cover: Persona stored on creation, fallback on Persona call failure, Persona present in the first interviewer prompt, fresh Persona on practice again.

## Comments

- 2026-09-28: The user is unsure whether to keep the database long term. Keeping it for now; nothing here should make removing it harder than it already is.
- 2026-09-28: Done. `prompts/persona.py` (Persona model, DEFAULT_PERSONA, prompt; the Job Description is left out so no company leaks in). `services/interview.create_persona`: one call with a JSON schema, no retry on bad output, falls back to Alex Morgan on LLMUnavailable or invalid JSON. `persona_name`/`persona_title` columns default to the fallback, so every Interview has a Persona. Interviewer prompt opens with "You are <name>, <title>" and asks for a first-name introduction; the Judge prompt is unchanged. `InterviewOut` and `frontend/lib/api.ts` carry the Persona; `HistoryRow` does not. `DevFakeLLMClient` returns Sam Taylor, Engineering Manager. Existing tests now script a Persona reply before every start; `tests/test_persona.py` adds 8 tests. 49 passed. Smoke run with `LLM_PROVIDER=fake` against a scratch DB returned the Persona. Local `interview.db` deleted; README note added under Configuration.
