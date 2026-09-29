# 05 Speech through gpt-audio-mini (backend and frontend)

Status: resolved
Blocked by: 02, 04

The dedicated speech models are not on the user's OpenRouter allow-list; `openai/gpt-audio-mini` is. The user chose to move both directions to it (ADR-0005).

- `speech.py`: speak through chat completions with audio output (streamed, pcm16 only), wrapped as WAV; refuse a reading whose transcript does not match the text, after one more try. Transcribe through chat completions with `input_audio`, instruction before the audio; `[silence]` becomes empty text.
- `routers/speech.py`: `audio/wav` responses; accept WAV and mp3 uploads only.
- Persona voices: six OpenAI voices, fallback `cedar`, dev fake `ash`. Local rows with Gemini voices moved to `cedar`.
- Frontend: `lib/wav.ts` converts every recording to 16 kHz mono WAV before upload.
- `STT_MODEL` and `TTS_MODEL` default to `openai/gpt-audio-mini`.

## Log

- 2026-09-29: Done. Prompts chosen from real calls: a plain "read this" prompt answered the Question instead of reading it (1/3 verbatim); "Say exactly: \"...\"" with a system prompt forbidding answers read 12/12 texts exactly. Transcription with the instruction after the audio failed 3/7; before it, 7/7 at 24 kHz and 7/7 at 16 kHz, and silence returned `[silence]`. All 13 OpenAI voices are accepted. Real round trip through the app client: speak 2.4 s, transcribe 1.2 s, word for word. Headless Chromium with a WAV as fake microphone, real models: first Question spoken (`audio/wav`, plays), recording converted and transcribed into the Answer box, Answer sent, next Question spoken. pytest 109 passed; tsc, lint pass.
