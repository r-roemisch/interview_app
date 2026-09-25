# Interview Practice: spec

Status: ready-for-agent
Confirmed by the user on 2026-09-25 after a grilling session. Vocabulary is defined in `CONTEXT.md`; architecture decisions in `docs/adr/`.

## Purpose

A single-user, local, capstone-grade web app where a candidate rehearses a behavioral job interview with an LLM interviewer and receives a structured Evaluation. English only, text only, no accounts, no deployment.

## Setup

- Job fields: title (required), industry (optional), Seniority (junior/mid/senior, defaults to mid), Job Description (optional free text pasted from a posting).
- Recommended Settings: from a pasted Job Description, one LLM call suggests title, industry and seniority. User reviews and may override each. Never applied silently.
- Difficulty: easy / normal / hard, default normal. Definitions in `CONTEXT.md`.
- Persona and interviewer pictures: out of scope (see Later).

## Interview

- Turn-based conversation, non-streaming. Follow-ups are Questions and count toward a cap of 10 Questions.
- First interviewer message = one-line greeting + first Question.
- No skipping. An empty Answer is still an Answer.
- "End interview" allowed once at least one Answer exists.
- After the 10th Answer or early end, the interviewer LLM writes a Closing (told explicitly if the candidate ended early). The Judge starts immediately in the background. The UI shows the Closing and a "See evaluation" button that enables when the Evaluation exists.
- Every Question, Answer and Closing is persisted as it happens. In Progress Interviews resume from History.
- LLM failure: 2 automatic retries, then error with a Retry button. Interview state must be unchanged on failure.
- Interview status: In Progress, Completed, Evaluation Missing.

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

## Stack

- Backend at repo root: uv, Python 3.12, FastAPI, SQLAlchemy 2 + SQLite (`create_all` at startup, no migrations), Pydantic v2, `openai` SDK with `base_url` = OpenRouter. Default model `google/gemma-4-31b-it:free`, env-configurable, no automatic fallback.
- Frontend in `frontend/`: Next.js App Router, TypeScript, Tailwind, no component library, every page `"use client"` (ADR-0001). Pages: Setup `/`, Interview `/interviews/[id]`, Evaluation `/interviews/[id]/evaluation`, History `/history`.
- Tests: pytest for backend with a fake LLM client. No frontend tests.
- `.env` replaced with only: `OPENROUTER_API_KEY`, `LLM_MODEL`, `DATABASE_URL`, `CORS_ORIGINS`, `NEXT_PUBLIC_API_URL`.

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

- `interviews`: id, title, industry, seniority, job_description, difficulty, status (`in_progress` / `completed` / `evaluation_missing`), created_at, ended_early (bool).
- `messages`: id, interview_id, role (`question` / `answer` / `closing`), text, position.
- `evaluations`: id, interview_id (unique), overall_score, justification, verdict, improvement_points (JSON), star_breakdowns (JSON: one per Answer with s/t/a/r ratings and comments), created_at.

## Later (explicitly out of scope)

Persona + pre-made interviewer pictures, voice input, streaming, image generation, technical interviews, timers, curated question bank, PDF export, other languages, multi-user, deployment, "jev".
