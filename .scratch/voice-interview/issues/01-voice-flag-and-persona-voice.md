# 01 Voice Interview flag and Persona voice (backend)

Status: resolved
Blocked by: none

Store whether an Interview is a Voice Interview, and give every Persona a voice. See spec "Setup" and "Persona voice", and `CONTEXT.md` (Voice Interview, Persona).

- `models.py`: `Interview.voice_interview` (bool, default false) and `Interview.persona_voice` (string, default the fallback Persona's voice).
- A fixed list of about 6 `gpt-4o-mini-tts` voices, each with a one-line description, and one of them as the fallback voice for "Alex Morgan, Hiring Manager" (e.g. next to `DEFAULT_PERSONA_*` in `models.py`).
- `prompts/persona.py`: the Persona model gets `voice`, an enum of the list; the prompt gives the descriptions and asks for the voice that fits the name. An unknown voice fails validation, so the whole Persona falls back, as today.
- `POST /interviews` takes `voice_interview`. "Practice again" copies it and gets a fresh Persona and voice.
- `InterviewOut` adds `voice_interview` and `persona_voice`. `HistoryRow` does not.
- `DevFakeLLMClient` returns a voice with its fake Persona. Existing tests that script a Persona reply need a voice added.
- Delete the local SQLite file once, and extend the README note.

Done when tests cover: voice stored from the Persona reply; unknown voice gives the fallback Persona with its fixed voice; `voice_interview` stored and copied by practice again, with a fresh Persona; `InterviewOut` carries both fields.

## Comments

- 2026-09-29: Done. `models.py`: `PERSONA_VOICES` (marin, cedar, coral, ash, sage, onyx, each with a short description), `DEFAULT_PERSONA_VOICE = "cedar"` for Alex Morgan, `Interview.persona_voice` and `Interview.voice_interview`. `prompts/persona.py`: `voice` is a `Literal` of the list, so the JSON schema has an enum and an unknown or missing voice falls back to the default Persona; the prompt lists the voices with descriptions. `POST /interviews` takes `voice_interview`; practice again copies it and gets a fresh Persona and voice. `InterviewOut` carries both fields, `HistoryRow` neither. Dev fake Persona speaks with `ash`. All test Persona replies now include a voice; 4 tests added to `tests/test_persona.py`; 91 passed. Real Persona calls picked fitting voices (Evelyn Hart: sage, Jonathan Meyers: ash, Maxwell Trent: onyx). Local `interview.db`: both columns added with `ALTER TABLE`, History kept. README note updated.
- 2026-09-29: Voices changed in issue 02: OpenAI's TTS is not on OpenRouter, so the list is now Gemini voices (Kore, Aoede, Leda, Charon, Orus, Puck), fallback Charon, dev fake Orus.
