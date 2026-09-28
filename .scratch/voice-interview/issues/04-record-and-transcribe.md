# 04 Record and transcribe Answers (frontend)

Status: resolved
Blocked by: 03

See spec "The candidate speaks".

- In a Voice Interview, a mic button next to the Answer box. Click to start and click to stop, with a recording indicator and elapsed time. Recording stops by itself at 5 minutes.
- Record with `MediaRecorder`, picking the first supported of `audio/webm;codecs=opus`, `audio/webm`, `audio/mp4` via `isTypeSupported`. Stop the mic tracks after each recording.
- On stop, post the audio to `/transcriptions` with a spinner on the mic button. Append the returned text to the Answer box (with a space if it already has text). Never send the Answer automatically.
- Errors, each shown briefly by the mic button, with typing still working: mic permission denied or no mic; transcription failed (record again or type).
- Disable the mic while a Question is loading or after the Interview has ended, the same as the Answer box.
- Explain the MediaRecorder and permission flow in short comments; the author is learning frontend.
- README agent section: describe Voice Interviews end to end.

Done when a manual run with `LLM_PROVIDER=fake` in Chrome and Firefox records, puts the fake sentence in the Answer box, sends it as a normal Answer, and shows the permission-denied message when the mic is blocked; `npm run lint` and `npm run build` pass.

## Comments

- 2026-09-29: Done in `app/interviews/[id]/page.tsx`. A `useRecorder` hook (getUserMedia, MediaRecorder with the first supported of webm/opus, webm, mp4; mic tracks released in `onstop`; a seconds counter that stops by itself at 5 minutes; recording dropped and mic released when leaving the page). The mic button sits next to Send only in a Voice Interview (Composer's optional `onTranscript`); it becomes a red square while recording and a spinner while transcribing. Recording status and errors reuse the hint line under the Answer box instead of new UI. The transcription is appended to the Answer box; nothing is sent automatically. `lib/api.ts`: `transcribe(blob)`. The button is labelled "Start recording" (not "Record your answer") so it cannot be confused with the Answer box's "Your answer" label. README agent section: Voice Interviews end to end. tsc, lint, build pass. Headless Chromium with a fake microphone and `LLM_PROVIDER=fake`: recording shows "Recording 0:01", stopping appends the fake sentence after the typed text, nothing is sent until Send, the Answer is stored as typed plus transcribed text; with the mic blocked the message shows and typing still works; written Interviews have no mic button. Not tested in Firefox (no Firefox in this environment) or with real speech models (not on the user's allow-list yet).
