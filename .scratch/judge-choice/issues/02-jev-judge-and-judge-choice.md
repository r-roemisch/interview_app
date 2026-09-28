# 02 JEV Judge and Judge choice (backend)

Status: resolved
Blocked by: 01

Each Interview gets a chosen Judge; the JEV Judge produces an Evaluation. See spec sections "Setup", "The JEV Judge", "History", "API", "Data model", and ADR-0003. Vocabulary: Judge, LLM Judge, JEV Judge, Checklist in `CONTEXT.md`.

- `models.py`:
  - `Judge` enum (`llm`, `jev`) and `Interview.judge`, default `llm`.
  - `Evaluation.judge`; unique on (`interview_id`, `judge`) instead of `interview_id`; `justification` nullable; `overall_confidence`, `verdict_confidence` nullable floats; `checklist` nullable JSON (list of `{check, probability}`); star breakdown JSON allows `comment: null` and a `confidence` per rating.
  - `Interview.evaluation` becomes the chosen Judge's Evaluation (e.g. a relationship filtered on the Interview's judge, or a property over an `evaluations` list).
- `POST /interviews` takes `judge`; "Practice again" copies it.
- JEV Judge (e.g. `prompts/jev_judge.py` for the state, questions and Checklist; `services/jev_judge.py` for the call and mapping):
  - State: Job snapshot and numbered transcript, as the LLM Judge gets it. No CV, no Persona.
  - Questions: four 5-level `score` questions per Answer, one 10-level `score` for the whole Interview, one `choice` for the Verdict, one yes/no per Checklist check. Use the Checklist from the spec as a constant list of `(check, improvement_point)`.
  - Mapping: rating = round(score) + 1; Overall Score = round(score / 9 × 100); Verdict from the choice; Improvement Points = wording of the three checks with the lowest yes-probability, lowest first; confidences stored.
  - Any failure, or a missing answer for any question, gives Evaluation Missing.
- `run_judge` and the background trigger dispatch on the Interview's Judge. The LLM Judge path is unchanged apart from storing `judge='llm'`. "Re-run evaluation" re-runs the chosen Judge.
- `EvaluationOut` adds `judge`, nullable `justification` and `comment`, the confidences and `checklist`. `GET /interviews/{id}/evaluation` keeps returning the chosen Judge's Evaluation.
- `HistoryRow` adds `judge`.
- Delete the local SQLite file once, and extend the README note.

Done when tests cover: the request has the right questions and no CV or Persona in the state; each mapping rule above; the three weakest checks become Improvement Points in order; JEV failure gives Evaluation Missing; rerun uses the chosen Judge; practice again copies the Judge; History rows carry it; existing LLM Judge tests still pass.

## Comments

- 2026-09-29: Done. `models.py`: `Judge` enum, `Interview.judge`, `Interview.evaluations` (list) with a read-only `evaluation` property for the chosen Judge and `evaluation_by(judge)`; `Evaluation.judge`, unique (`interview_id`, `judge`), nullable `justification`, `overall_confidence`, `verdict_confidence`, `checklist`. `services/judge.py`: `evaluate(judge, ...)` picks the Judge (issue 03 reuses it), `replace_evaluation` deletes and flushes the old row before adding the new one so the unique constraint never sees two rows; `run_judge` takes an optional `jev`. `prompts/jev_judge.py` holds the Checklist, levels, question keys and state (reuses `job_block`/`transcript_block`, now public in `prompts/judge.py`); `services/jev_judge.py` maps answers to an Evaluation and returns None on any failure. Router passes a `JevClient` dependency to the background Judge; conftest adds a `jev` fixture. `InterviewOut`, `HistoryRow` and `EvaluationOut` carry `judge`. `tests/test_jev_judge.py` 8 tests; 82 passed. Local `interview.db`: backed up, `interviews.judge` added, `evaluations` rebuilt (SQLite cannot drop NOT NULL in place); the one Interview was kept. Real run (gpt-4.1-mini interviewer, real JEV): a strong Answer got STAR 4-5, a vague one 1s, Overall 27, no_hire at 0.95 confidence, sensible Improvement Points.
