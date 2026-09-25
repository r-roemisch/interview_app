# 07 History, delete and practice-again API

Status: ready-for-agent
Blocked by: 05

`GET /interviews` → list of `HistoryRow` (id, title, created_at, status, overall_score or null) newest first. `DELETE /interviews/{id}` cascades messages and evaluation. `POST /interviews/{id}/practice-again` creates a new Interview from the same Job snapshot and Difficulty, exactly like `POST /interviews` (including first Question).

Done when tests cover list ordering, delete cascade, and practice-again producing a new in_progress Interview.
