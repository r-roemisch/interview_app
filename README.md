<!-- OWNER SECTION START: written by the owner. Agents leave everything up to OWNER SECTION END unchanged. -->
# Interview Practice

A single-user web app for rehearsing behavioral job interviews. An LLM plays the interviewer, asks up to ten questions with follow-ups, and a separate LLM judge scores every answer against STAR (Situation, Task, Action, Result), gives an overall score, a hiring verdict and three improvement points.

The vocabulary used in the code and docs is defined in [`CONTEXT.md`](./CONTEXT.md). Architecture decisions are in [`docs/adr/`](./docs/adr/).

## How it works

1. **Setup**: enter the job title, optional industry, seniority and job description, and pick a difficulty. Pasting a job description lets the app suggest title, industry and seniority.
2. **Interview**: the interviewer greets you and asks the first question. Answer in text. Follow-ups count toward the cap of ten. You can end early after at least one answer.
3. **Closing and judging**: after the last answer the interviewer writes a closing message and the judge starts in the background. When it finishes, "See evaluation" lights up.
4. **Evaluation**: overall score, verdict and justification, then the transcript with a STAR breakdown under every answer, then three improvement points. "Practice this job again" starts a fresh interview with the same settings.
5. **History**: all past interviews with status and score. In-progress ones can be resumed.

## Not in this version

Interviewer personas and pictures, voice input, streaming replies, technical interviews, timed answers, a curated question bank, PDF export, other languages, multiple users and deployment.

<!-- OWNER SECTION END -->

<!-- AGENT SECTION START: maintained by Claude and kept in sync with the code. -->

## Stack

| Part | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, SQLite, OpenAI SDK pointed at OpenRouter |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind v4 |
| Tests | pytest with a scripted fake LLM (no network, no key) |

The frontend is a thin client. Every page is a client component and all logic, including LLM calls, lives in the FastAPI backend (see ADR-0001).

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (installs Python 3.12 for you)
- Node.js 22 and npm
- Optionally an [OpenRouter](https://openrouter.ai/keys) API key. Without one, use the offline fake model described below.

## Setup

```bash
git clone <this repo> interview_app
cd interview_app

# backend
uv sync
cp .env.example .env          # then edit, see "Configuration"

# frontend
cd frontend
npm install
cp .env.example .env.local    # default points at http://localhost:8000
cd ..
```

## Run

Two terminals, both from the repo root.

```bash
# terminal 1: backend on http://localhost:8000
uv run interview-app

# terminal 2: frontend on http://localhost:3000
cd frontend && npm run dev
```

Open http://localhost:3000. The dot in the top-right corner turns green when the frontend can reach the backend. API docs are at http://localhost:8000/docs.

## Configuration

Backend, in `.env` at the repo root:

| Variable | Default | Meaning |
|---|---|---|
| `LLM_PROVIDER` | `openrouter` | `openrouter` for real calls, `fake` for an offline scripted interviewer and judge |
| `OPENROUTER_API_KEY` | empty | Required when `LLM_PROVIDER=openrouter` |
| `LLM_MODEL` | `google/gemma-4-31b-it:free` | Any OpenRouter model id. Free ones are listed at https://openrouter.ai/models?q=free |
| `DATABASE_URL` | `sqlite:///./interview.db` | SQLAlchemy URL. The SQLite file is created on first start |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated origins allowed to call the API |

Frontend, in `frontend/.env.local`:

| Variable | Default | Meaning |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Where the browser finds the backend. Baked in at build time, so restart `npm run dev` after changing it |

### After a change to the tables

There are no migrations: at startup the backend creates missing tables but never adds columns to existing ones. When a change adds columns (the Persona did), delete `interview.db` and restart the backend. This also deletes your History.

### "Model blocked by guardrail"

If every request fails with this message, your OpenRouter workspace restricts which models a key may use. Two common causes:

- **An allow-list guardrail** on the workspace. Only the listed models work, free or paid. Check which ones your key may use with `curl https://openrouter.ai/api/v1/models/user -H "Authorization: Bearer $OPENROUTER_API_KEY"` and set `LLM_MODEL` to one of them. `openai/gpt-4.1-mini` is a good, cheap choice that handles the judge's JSON well.
- **The data policy** that blocks free models because they may train on prompts. Allow free endpoints in the privacy settings.

Both are configured at https://openrouter.ai/workspaces/default/guardrails. Free models are also rate-limited; the app retries twice and then shows a Retry button.

### Developing without a key

Set `LLM_PROVIDER=fake`. The backend then uses a fixed Persona (Sam Taylor, Engineering Manager), asks ten fixed behavioral questions, writes a closing message and returns a fixed evaluation. Everything else, including history, resume, re-run and delete, behaves exactly as with a real model.

## Tests

```bash
uv run pytest
```

The tests use a fake LLM with scripted replies, so they need no key and make no network calls. There are no frontend tests. To check the frontend:

```bash
cd frontend
npx tsc --noEmit && npm run lint && npm run build
```

## Project layout

```
src/interview_app/
  main.py           app factory, CORS, /health
  config.py         settings from .env
  db.py             engine, session, table creation
  models.py         Interview, Message, Evaluation
  schemas.py        API response shapes
  llm.py            OpenRouter client, retries, fake clients
  prompts/          interviewer, Persona, judge, recommended-settings prompts
  services/         interview flow, judge, recommendation
  routers/          HTTP endpoints
tests/              pytest suite
frontend/
  app/              pages (all "use client"), layout, nav, shared ui
  lib/api.ts        typed client for the backend
docs/adr/           architecture decisions
.scratch/           spec and implementation issues
```

<!-- AGENT SECTION END -->
