# Speech goes through an audio chat model, prompted to read aloud and to transcribe

The interviewer's voice and the transcription of spoken Answers both use `openai/gpt-audio-mini`, a chat model that hears and speaks, instead of dedicated text-to-speech and transcription models. The dedicated ones (`google/gemini-3.8-flash-tts`, `openai/gpt-4o-mini-transcribe`) are not on the user's OpenRouter allow-list and `gpt-audio-mini` is, so the user chose it on 2026-09-29. It still goes through FastAPI and OpenRouter (ADR-0004); only the kind of model changes.

A chat model does what it is asked rather than what it is given, so both directions depend on a prompt, checked with real calls before this decision:

- **Speaking**: asked to "say exactly" a quoted text. Without that framing it answered the interviewer's Question in the candidate's place. The reply carries a transcript of what was spoken; a reading that differs from the text by more than 20% of its words is tried once more and then refused, so the text on screen is all the candidate gets.
- **Transcribing**: the instruction must come before the audio in the message, or the model often claims it received none. Silence comes back as the marker `[silence]`, which becomes an empty Answer.

## Consequences

- Audio output is only available streamed and only as raw 16-bit PCM at 24 kHz. The backend collects the stream and serves it as WAV (`audio/wav`), so a Question is heard only once all of it has been generated (about 2-3 s).
- The model cannot read webm or mp4, the formats browsers record, so the frontend converts every recording to a 16 kHz mono WAV (`lib/wav.ts`) before uploading it.
- The Persona voices are OpenAI's voices. Existing local Interviews with Gemini voice names were moved to the fallback voice.
- `TTS_MODEL` and `STT_MODEL` stay separate settings, but both must now be audio chat models: switching back to dedicated speech models means restoring the previous `speech.py`, not just changing `.env`.
