# 07 History, delete and practice-again API

Status: resolved
Blocked by: 05

`GET /interviews` → list of `HistoryRow` (id, title, created_at, status, overall_score or null) newest first. `DELETE /interviews/{id}` cascades messages and evaluation. `POST /interviews/{id}/practice-again` creates a new Interview from the same Job snapshot and Difficulty, exactly like `POST /interviews` (including first Question).

Done when tests cover list ordering, delete cascade, and practice-again producing a new in_progress Interview.

## Comments

- 2026-09-25: Done. In `routers/interviews.py`: `GET /interviews` (HistoryRow, newest first, score from Evaluation if any), `DELETE /interviews/{id}` (204, cascade via ORM relationships), `POST /interviews/{id}/practice-again` (201, reuses `start_interview` with the Job snapshot and Difficulty). 3 tests. Shared `strip_code_fence` moved to `llm.py`.
