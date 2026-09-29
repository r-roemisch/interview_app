# 01 Portrait generation and storage (backend)

Status: resolved
Blocked by: none

See spec "Setup", "The Portrait", "Generation", "Storage", "API" and "Config"; `CONTEXT.md` (Portrait).

- An image client next to `speech.py` (e.g. `images.py`): `portrait(prompt) -> bytes` (PNG). Real one with the `openai` SDK against OpenRouter chat completions (`modalities=["image", "text"]`; the image arrives as a base64 data URL in `message.images`), retries through `llm.call_with_retries`. A scripted fake for tests and a dev fake returning a fixed placeholder PNG. `get_image_client` dependency, `IMAGE_MODEL` setting.
- Prompt (e.g. `prompts/portrait.py`): from the Persona's name and title, the Job's industry, and "woman"/"man" from the voice description in `PERSONA_VOICES`. Never the CV or the Job Description.
- A `portraits` table: one row per Interview that asked for a Portrait, with its state (`pending`/`ready`/`failed`) and the PNG. Cascade delete with the Interview.
- `POST /interviews` takes `portrait` (default true); the row starts `pending` and a background task (own session, like the Judge) generates it: one more try after a failure, then `failed`. Practice again copies whether a row existed.
- Startup: `pending` rows become `failed` (next to `fail_interrupted_judges`).
- `InterviewOut.portrait` (`none`/`pending`/`ready`/`failed`); `GET /interviews/{id}/portrait` serves `image/png`, 404 unless ready.
- `.env.example`, README agent section (config table, layout, what a Portrait is).

Done when the tests in the spec pass.

## Comments

- 2026-09-29: Done. `images.py` (`OpenRouterImageClient`: chat completions with `modalities=["image", "text"]`, the image read from `message.images` as a data URL, PNG/JPEG/WebP accepted by their first bytes; `FakeImageClient`; `DevFakeImageClient` returns a hand-built placeholder PNG after 2 s), `prompts/portrait.py` (name, title, industry, woman/man from the voice, "fictional"), `models.Portrait` (own table, image deferred), `services/portrait.py` (background generation with one more try, `fail_unfinished_portraits` at startup), `InterviewOut.portrait`, `GET /interviews/{id}/portrait`, `IMAGE_MODEL`. `tests/test_portrait.py` 12 tests; 120 passed. `tests/conftest.py` now sets `LLM_PROVIDER=fake` before importing the app: the first run lacked the image fake and made real image calls with the key from `.env`, which the guard now makes impossible.
- Real calls: without "fictional" one Persona (Lena Hartman) got no image twice in a row in the background, while the same prompt worked when repeated by hand; the model's text is now kept in the error for the log. With "fictional", 4/4 Personas succeeded in 6-11 s (PNG, 1.2-1.6 MB).
