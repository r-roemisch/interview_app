# 03 Data model

Status: resolved
Blocked by: 01

`models.py` with SQLAlchemy tables `interviews`, `messages`, `evaluations` exactly as in the spec's Data model section. Enums for status, role, seniority, difficulty, verdict. `schemas.py` with Pydantic response models: `InterviewOut` (fields + transcript + status + question_count), `HistoryRow`, `EvaluationOut`, `StarBreakdown`.

Done when a test creates an Interview with messages and an Evaluation and reads it back.

## Comments

- 2026-09-25: Done. `models.py` (Interview, Message, Evaluation; StrEnums for seniority, difficulty, status, role, verdict; `QUESTION_CAP = 10`; cascade deletes; `question_count`/`answer_count` helpers) and `schemas.py` (MessageOut, InterviewOut, HistoryRow, StarRating, StarBreakdown, EvaluationOut). Added a `judging` status for the window between Closing and Evaluation; glossary and spec updated. 3 tests: round trip, defaults, cascade.
