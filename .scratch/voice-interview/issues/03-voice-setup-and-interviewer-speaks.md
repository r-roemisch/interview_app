# 03 Voice Interview choice and the interviewer speaks (frontend)

Status: resolved
Blocked by: 02

See spec "Setup" and "The interviewer speaks".

- Setup: a choice between "Written interview" (default) and "Voice interview", styled like the Difficulty choice. Send `voice_interview`.
- Interview page, only when `voice_interview` is true:
  - Each new Question and the Closing play automatically once, from `/interviews/{id}/messages/{message_id}/speech`, when they arrive in this page session. Resuming does not replay old messages.
  - A replay button on every interviewer message.
  - A "Mute interviewer" toggle in the side panel, kept in component state only.
  - Any playback failure (fetch error, 503, browser autoplay block) is silent: the text is shown and replay tries again.
- Written Interviews look exactly as today.
- `frontend/lib/api.ts`: `voice_interview` and `persona_voice` on the Interview, a `speechUrl(interviewId, messageId)` helper.

Done when a manual run with `LLM_PROVIDER=fake` shows a Voice Interview that plays (silent) audio per Question with working replay and mute, a written Interview unchanged, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-09-29: Done. Setup: "Interview" choice (Written default / Voice) via the existing `ChoiceCards` and `MODE_OPTIONS` in `lib/labels.ts`. Interview page: a module-level `play()` keeps one `Audio` in a ref and swallows every playback error; an effect speaks the newest unspoken interviewer message, tracking spoken ids in a ref. On first load a fresh Interview (no Answers yet) speaks its first Question, a resumed one stays quiet. Replay icon on each Question and the Closing (`Entry` got an optional `onPlay`), "Mute interviewer" in the side panel (state only; muting pauses the current audio, unmuting does not replay). Audio stops when leaving the page. `lib/api.ts`: `voice_interview`, `persona_voice`, `speechUrl`. tsc, lint, build pass. Headless Chromium with `LLM_PROVIDER=fake`, counting speech requests: fresh Interview spoke Q1; the next Question was spoken after sending; replay fetched it again; while muted nothing was fetched; after reload nothing was fetched; the dev fake's silent mp3 decodes (0.26 s).
