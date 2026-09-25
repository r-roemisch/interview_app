# 03 Data model

Status: ready-for-agent
Blocked by: 01

`models.py` with SQLAlchemy tables `interviews`, `messages`, `evaluations` exactly as in the spec's Data model section. Enums for status, role, seniority, difficulty, verdict. `schemas.py` with Pydantic response models: `InterviewOut` (fields + transcript + status + question_count), `HistoryRow`, `EvaluationOut`, `StarBreakdown`.

Done when a test creates an Interview with messages and an Evaluation and reads it back.
