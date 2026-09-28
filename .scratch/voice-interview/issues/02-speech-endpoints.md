# 02 Speech client and endpoints (backend)

Status: resolved
Blocked by: 01

Text-to-speech and transcription through OpenRouter. See spec "The interviewer speaks", "The candidate speaks", "API", "Config", and ADR-0004.

- A speech client (e.g. `interview_app/speech.py`) with a protocol of two methods, `speak(text, voice) -> bytes` (mp3) and `transcribe(audio, filename, content_type) -> str`. Real implementation with the `openai` SDK against OpenRouter (`audio.speech.create` with `response_format="mp3"`, `audio.transcriptions.create`). Check OpenRouter's docs for the exact request shape of both endpoints before relying on the SDK defaults.
- Same retry policy and single failure exception as `OpenRouterClient`; the allow-list rejection message from judge-choice issue 01 applies.
- Config: `STT_MODEL` (default `openai/gpt-4o-mini-transcribe`), `TTS_MODEL` (default `openai/gpt-4o-mini-tts`), in `config.py` and `.env.example`.
- Fakes: a scripted one for tests, and a dev fake for `LLM_PROVIDER=fake` (TTS returns a short silent mp3 kept in the repo or generated; STT returns a fixed sentence).
- `GET /interviews/{id}/messages/{message_id}/speech`: `audio/mpeg` for a Question or Closing in the Interview's Persona voice; 404 for an Answer or a message of another Interview; 503 if TTS fails. Nothing stored.
- `POST /transcriptions`: multipart `file`; accept webm, ogg, mp4/m4a, mp3, wav; 422 for other types or over 25 MB; returns `{text}` stripped; 503 if transcription fails. Nothing stored.
- README agent section: the two env vars and that both models must be on the allow-list.

Done when tests cover: speech uses the Persona's voice and returns `audio/mpeg`; 404 for an Answer; 503 on TTS failure; transcription returns the fake text; unsupported and oversized files give 422; 503 on transcription failure.

## Comments

- 2026-09-29: Done. OpenAI's TTS models are not on OpenRouter any more (`openai/gpt-4o-mini-tts` "does not exist"); the user chose `google/gemini-3.8-flash-tts`, so `PERSONA_VOICES` became Gemini voices (see issue 01) and existing local rows were set to Charon. `speech.py`: `SpeechClient` protocol, `OpenRouterSpeechClient` (openai SDK `audio.speech.create` with mp3 and `audio.transcriptions.create`), `FakeSpeechClient`, `DevFakeSpeechClient` (ten silent MP3 frames, fixed sentence), `get_speech_client`. The retry loop moved out of `OpenRouterClient` into `llm.call_with_retries`, shared by chat and speech. `routers/speech.py`: `GET /interviews/{id}/messages/{message_id}/speech` and `POST /transcriptions` (the content type picks the file extension the model reads, e.g. `audio/mp4` becomes `answer.m4a`). `STT_MODEL`/`TTS_MODEL` in config, `.env.example`, README. `tests/test_speech.py` 10 tests; 101 passed. Real calls with the user's key return the allow-list message for both models, so the user must add them.
