# Voice Interview: spec

Status: ready-for-agent
Confirmed by the user on 2026-09-28 after a grilling session. Build order: last, after `cv-and-pdf-upload` and `judge-choice`. Vocabulary in `CONTEXT.md` (Voice Interview, Answer, Persona). Decision record: ADR-0004. Extends `.scratch/interview-practice/spec.md`.

## Purpose

Rehearse out loud. The interviewer speaks its Questions and the Closing, the candidate answers by speaking, and afterwards the transcript and Evaluation are the same as for a written Interview.

## Setup

- Setup offers a choice: **Written interview** (default) or **Voice interview**. Stored on the Interview; cannot be switched after Setup. Resuming from History keeps it. "Practice again" copies it.

## Persona voice

- Every Persona gets one voice from a fixed list of about 6 `gpt-4o-mini-tts` voices, each with a one-line description so the voice can fit the Persona's name.
- The Persona call returns the voice together with name and title (an enum in its JSON schema). The fallback Persona "Alex Morgan, Hiring Manager" has a fixed voice. An unknown voice in the reply counts as a failed Persona call (fallback).
- Stored for every Interview (harmless for written ones). "Practice again" gets a fresh Persona and voice, as today.
- The voice decides who is speaking, never how: no tone instructions from Difficulty go to TTS.

## The interviewer speaks

- Text-to-speech through OpenRouter, model `openai/gpt-4o-mini-tts`, mp3 output, the Persona's voice.
- Each new Question and the Closing play automatically when they arrive. Every interviewer message has a replay button.
- The Question text is always shown, as in a written Interview.
- A "Mute interviewer" toggle on the Interview page stops automatic playback. It is not stored; a page reload unmutes.
- If speech fails (network, model, browser autoplay block), nothing breaks: the text is there and the replay button tries again. No error screen.
- No audio is stored. Speech is generated on request.

## The candidate speaks

- A mic button next to the Answer box: click to start recording, click to stop. A visible recording indicator and elapsed time.
- The browser records with `MediaRecorder`, choosing a format with `isTypeSupported` (webm/opus, else mp4).
- On stop, the audio is sent to the backend, which transcribes it through OpenRouter, model `openai/gpt-4o-mini-transcribe`. The text is added to the Answer box (appended if the box already has text) and the candidate edits it and presses send. Nothing is sent automatically.
- The Answer box and send button work exactly as in a written Interview, so typing is always possible.
- Mic permission denied or no mic: show a short message by the mic button; typing still works.
- Transcription fails: an error by the mic button; record again or type.
- Max recording length 5 minutes (stops automatically), max upload 25 MB.

## Transcript

- Answers are stored as the text the candidate sent, like any Answer. The Evaluation page transcript is unchanged. No audio kept, no download.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/interviews` | adds `voice_interview`: bool, default false |
| GET | `/interviews/{id}/messages/{message_id}/speech` | `audio/mpeg` for a Question or Closing, in the Persona's voice; 404 for an Answer; 503 if TTS fails |
| POST | `/transcriptions` | multipart `file` (audio) → `{text}`; 422 for unsupported format or too large; 503 if transcription fails |

`InterviewOut` adds `voice_interview` and `persona_voice`.

## Data model

- `interviews.voice_interview`: bool, default false.
- `interviews.persona_voice`: string, default the fallback Persona's voice.
- Delete the local SQLite file once; README note.

## Config

- `STT_MODEL`, default `openai/gpt-4o-mini-transcribe`. `TTS_MODEL`, default `openai/gpt-4o-mini-tts`.
- `LLM_PROVIDER=fake` also fakes both: TTS returns a short silent mp3, STT returns a fixed sentence.
- README: the user must add both model ids to the OpenRouter allow-list. The blocked-model error message from `judge-choice` covers these models too.

## Tests

Backend with fake speech clients:
- Persona call returns a voice from the list; unknown voice → fallback Persona with its fixed voice; practice again gets a fresh voice and copies `voice_interview`.
- Speech endpoint uses the Persona's voice, returns `audio/mpeg`, 404 for an Answer, 503 when TTS fails.
- Transcription endpoint returns the fake text, rejects oversized or unsupported files, 503 on failure.
- A Voice Interview's Answers and Evaluation behave exactly like a written Interview's.

## Out of scope

Live text while speaking, automatic end-of-speech detection, auto-sending Answers, storing or downloading audio, streaming TTS, Difficulty-dependent tone of voice, switching modes mid-Interview.
