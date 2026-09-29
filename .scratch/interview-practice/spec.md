# Interview Practice: spec

Status: resolved
Confirmed by the user on 2026-09-25 after a grilling session; Persona and UI sections added after a second grilling session on 2026-09-28. Vocabulary is defined in `CONTEXT.md`; architecture decisions in `docs/adr/`.
Extended on 2026-09-28 by `.scratch/cv-and-pdf-upload/spec.md`, `.scratch/judge-choice/spec.md` and `.scratch/voice-interview/spec.md`; where they differ, they win.

## Purpose

A single-user, local, capstone-grade web app where a candidate rehearses a behavioral job interview with an LLM interviewer and receives a structured Evaluation. English only, no accounts, no deployment. Written Interviews by default; Voice Interviews are specified in `voice-interview`.

## Setup

- Job fields: title (required), industry (optional), Seniority (junior/mid/senior, defaults to mid), Job Description (optional free text pasted from a posting).
- Recommended Settings: from a pasted Job Description, one LLM call suggests title, industry and seniority. User reviews and may override each. Never applied silently.
- Difficulty: easy / normal / hard, default normal. Definitions in `CONTEXT.md`.
- The user does not choose the Persona (see Persona).

## Persona

- Each Interview gets its own Persona: a name and job title (no company), invented by the LLM to fit the Job, e.g. "Priya Nair, Head of Customer Success".
- Created in `start_interview` by a separate small LLM call returning JSON `{name, title}`, before the first Question. The first Question prompt receives it.
- If that call fails after retries, fall back to "Alex Morgan, Hiring Manager" and continue. The first Question call keeps the normal retry-then-error behaviour.
- The interviewer prompt knows the Persona's name and title only. Tone and strictness stay with Difficulty.
- Stored on the Interview; not editable, no re-roll. "Practice again" gets a fresh Persona.
- Shown as initials in a circle plus name and title on the Interview page and on Questions in the Evaluation transcript. The Evaluation itself is labelled Judge. History rows do not show it.

## Interview

- Turn-based conversation, non-streaming. Follow-ups are Questions and count toward a cap of 10 Questions.
- First interviewer message = one-line greeting + first Question.
- No skipping. An empty Answer is still an Answer.
- "End interview" allowed once at least one Answer exists.
- After the 10th Answer or early end, the interviewer LLM writes a Closing (told explicitly if the candidate ended early). The Judge starts immediately in the background. The UI shows the Closing and a "See evaluation" button that enables when the Evaluation exists.
- Every Question, Answer and Closing is persisted as it happens. In Progress Interviews resume from History.
- LLM failure: 2 automatic retries, then error with a Retry button. Interview state must be unchanged on failure.
- Interview status: In Progress, Judging (Closing given, Judge running), Completed, Evaluation Missing.

## Evaluation

- Separate Judge prompt (ADR-0002). Input: Job snapshot + full transcript. Output validated with Pydantic; one retry on validation failure, then status Evaluation Missing with a "Re-run evaluation" action.
- Per Answer: STAR Breakdown, S/T/A/R each 1-5 with a one-line comment.
- Overall Score 0-100 assigned holistically by the Judge, with a one-paragraph justification.
- Recommendation: Verdict (strong_hire / hire / no_hire) + exactly three Improvement Points.
- Evaluation page shows each STAR Breakdown inline under its Question and Answer.

## History

- Rows: job title, created date, status, Overall Score (if any).
- Completed opens the Evaluation; In Progress resumes; Evaluation Missing opens a page with the Re-run action.
- Delete with confirmation.
- "Practice again" on an Evaluation copies the Job snapshot and Difficulty into a new Interview.

## UI

- Polished SaaS look: a cool, softly tinted page with a faint indigo glow at the top (not plain white), indigo as the one accent colour, white cards with soft shadows and light borders on top of it, the top bar and the Interview side panel slightly see-through, icons from `lucide-react` (the only UI dependency). The background is static and has a matching dark version. Chosen from prototypes (issue 17). Interview page is a full-height chat with the Answer box pinned to the bottom.
- Layouts may change; flows and URLs stay as listed in Stack.
- Light/dark follows the system setting, no toggle. Desktop first; mobile must stay usable.
- The layout is chosen from throwaway prototypes of the Interview page (issue 14), then applied to all pages (issue 16).

## Stack

- Backend at repo root: uv, Python 3.12, FastAPI, SQLAlchemy 2 + SQLite (`create_all` at startup, no migrations), Pydantic v2, `openai` SDK with `base_url` = OpenRouter. Default model `google/gemma-4-31b-it:free`, env-configurable, no automatic fallback.
- Frontend in `frontend/`: Next.js App Router, TypeScript, Tailwind, no component library, every page `"use client"` (ADR-0001). Pages: Setup `/`, Interview `/interviews/[id]`, Evaluation `/interviews/[id]/evaluation`, History `/history`.
- Tests: pytest for backend with a fake LLM client. No frontend tests.
- `.env` replaced with only: `LLM_PROVIDER` (`openrouter` or `fake`, an offline scripted model for development), `OPENROUTER_API_KEY`, `LLM_MODEL`, `DATABASE_URL`, `CORS_ORIGINS`; frontend `.env.local` has `NEXT_PUBLIC_API_URL`.

## API (JSON, no auth)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/recommend-settings` | `{job_description}` → `{title, industry, seniority}` |
| POST | `/interviews` | `{title, industry?, seniority, job_description?, difficulty}` → Interview with first Question |
| GET | `/interviews` | History rows |
| GET | `/interviews/{id}` | Interview with transcript and status |
| POST | `/interviews/{id}/answers` | `{text}` → next Question, or Closing if cap reached |
| POST | `/interviews/{id}/end` | early end → Closing |
| GET | `/interviews/{id}/evaluation` | 404 while pending, 200 with Evaluation, 409 if Evaluation Missing |
| POST | `/interviews/{id}/evaluation/rerun` | re-run the Judge |
| POST | `/interviews/{id}/practice-again` | new Interview from the same Job snapshot |
| DELETE | `/interviews/{id}` | delete |

## Data model

- `interviews`: id, title, industry, seniority, job_description, difficulty, persona_name, persona_title, status (`in_progress` / `judging` / `completed` / `evaluation_missing`), created_at, ended_early (bool).
- `messages`: id, interview_id, role (`question` / `answer` / `closing`), text, position.
- `evaluations`: id, interview_id (unique), overall_score, justification, verdict, improvement_points (JSON), star_breakdowns (JSON: one per Answer with s/t/a/r ratings and comments), created_at.

## Later (explicitly out of scope)

Interviewer pictures (Persona uses initials only), Persona personalities, streaming, image generation, technical interviews, timers, curated question bank, PDF export, other languages, multi-user, deployment. (Voice input and the JEV Judge moved into their own specs.)
