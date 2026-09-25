# 01 Backend skeleton and config

Status: resolved
Blocked by: none

Add FastAPI, SQLAlchemy 2, Pydantic v2, pydantic-settings, openai, pytest, httpx to `pyproject.toml` via uv. Create `src/interview_app/` modules: `config.py` (settings from env: `OPENROUTER_API_KEY`, `LLM_MODEL` default `google/gemma-4-31b-it:free`, `DATABASE_URL` default `sqlite:///./interview.db`, `CORS_ORIGINS` default `http://localhost:3000`), `db.py` (engine, session dependency, `create_all` on startup), `main.py` (app factory, CORS, `GET /health`). Replace the template `.env` with `.env.example` holding only the keys in the spec; keep `.env` git-ignored. Add `tests/conftest.py` with an in-memory SQLite fixture and a TestClient. Run command: `uv run uvicorn interview_app.main:app --reload`.

Done when `uv run pytest` passes a health-check test.

## Comments

- 2026-09-25: Done. Added `config.py`, `db.py`, `models.py` (stub), `main.py` with `/health` and CORS; `tests/conftest.py` with in-memory SQLite + TestClient; `.env.example` with the five keys; `.env` reset to the example (old template held only placeholder keys, backup kept in the session scratchpad). Console script is now `interview_app.main:run`. `uv run pytest` passes 2 tests; server smoke-tested on port 8765.
