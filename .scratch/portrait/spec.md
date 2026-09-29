# Portrait: spec

Status: resolved
Confirmed by the user on 2026-09-29 after a grilling session. Vocabulary in `CONTEXT.md` (Persona, Portrait). Extends `.scratch/interview-practice/spec.md`, which listed interviewer pictures and image generation as out of scope; this spec brings them in.

## Purpose

Give the interviewer a face. A Portrait of the Persona sits next to the conversation for the whole Interview, so a rehearsal feels closer to talking to a real person.

## Setup

- A switch "Show a portrait of the interviewer (about 4 cents)", on by default, next to the Written/Voice choice. Stored on the Interview.
- "Practice again" copies the switch. It gets a new Persona, and so a new Portrait.

## The Portrait

- A photorealistic head-and-shoulders headshot of a fictional person: soft neutral background, natural light, friendly and professional, no text or logos. ("Fictional": a named person otherwise reads as a real one, which the model may refuse.)
- Made to fit the Persona's name and job title, the Job's industry when there is one, and whether the Persona's voice is female- or male-sounding, so that face and voice match. The voice is picked for every Interview, written or Voice.
- Never from the CV or the Job Description: like the Persona call, the Portrait has no company.
- Model `google/gemini-2.5-flash-image` through OpenRouter (the only image model on the user's allow-list, checked 2026-09-29): about $0.04 and 7 s per Portrait, a 1024×1024 PNG of about 1.3 MB.

## Generation

- Starts in the background right after the Persona is invented; the Interview starts as fast as without a Portrait. It never blocks or fails an Interview.
- While it is being made, the Persona's initials show with a soft loading shimmer; the Portrait fades in when ready.
- A failed attempt (model unavailable, refused, no image in the reply) is tried once more; after that the Interview keeps the initials for good. No "try again" and no re-roll (the Persona has none either).
- A server restart while a Portrait is being made loses it: at startup every unfinished Portrait counts as failed.
- `LLM_PROVIDER=fake`: a fixed placeholder Portrait, no network.

## Storage

- Saved once per Interview, as generated (usually PNG; JPEG and WebP are accepted too), in its own table: the image and its state (being made, ready, failed). No row means no Portrait was asked for.
- A new table is created at startup without touching existing ones, so the local `interview.db` does not have to be deleted.
- Deleting an Interview deletes its Portrait. Interviews from before this feature have none and show initials.

## Where it shows

- Interview page: the side panel moves to the **left**. At its top, the Portrait as a large rounded square filling the panel's width (about 280 px), with the Persona's name and title underneath; the Job details, Question tracker and STAR reminder follow.
- Interview page below `lg` (the folded strip at the top): the Portrait small, in place of the initials.
- Evaluation page, next to "Questions asked by …": the Portrait small, in place of the initials.
- Not in History (the spec keeps the Persona out of History rows).
- Without a Portrait (switched off, failed, or older Interviews): initials, as today.

## API

| Method | Path | Change |
|---|---|---|
| POST | `/interviews` | adds `portrait`: bool, default true |
| POST | `/interviews/{id}/practice-again` | copies whether a Portrait was asked for |
| GET | `/interviews/{id}` | `InterviewOut` adds `portrait`: `none` \| `pending` \| `ready` \| `failed` |
| GET | `/interviews/{id}/portrait` | `image/png`; 404 unless `ready` |

`HistoryRow` does not change.

## Config

- `IMAGE_MODEL`, default `google/gemini-2.5-flash-image`.

## Tests

Backend with a fake image client:
- `portrait: true` → `pending` right after start, `ready` after the background task, and the image is served as `image/png`; `portrait: false` → `none` and no image call.
- A first failure then success → `ready`; two failures → `failed`, and the Interview is unaffected.
- The prompt contains the Persona's name and title, the industry, and the voice's woman/man hint; never the CV or the Job Description.
- Practice again copies the switch and makes a new Portrait for the new Persona.
- At startup, `pending` becomes `failed`. Deleting an Interview deletes its Portrait.

## Out of scope

Re-rolling or editing a Portrait, choosing a style, Portraits in History, shrinking or converting the image, animated or speaking faces.
