# 05 Judge and Evaluation API

Status: ready-for-agent
Blocked by: 04

`prompts/judge.py`: prompt receiving Job snapshot and full transcript, instructing STAR ratings 1-5 with one-line comment per Answer, Overall Score 0-100 with one-paragraph justification, Verdict, exactly three Improvement Points, output as JSON matching a Pydantic `JudgeOutput` model. Pass the JSON schema via `response_format` where the model supports it, and also embed it in the prompt.

`services/judge.py`: run Judge, validate with Pydantic, one retry on `ValidationError`, on success persist Evaluation and set status completed, on failure set status evaluation_missing. Triggered as a FastAPI `BackgroundTask` right after the Closing is persisted (from issue 04's end and answers endpoints).

Routes: `GET /interviews/{id}/evaluation` (404 pending, 200 with `EvaluationOut`, 409 evaluation_missing), `POST /interviews/{id}/evaluation/rerun` (only when completed or evaluation_missing).

Done when tests cover: valid Judge JSON → completed, invalid then valid → completed, twice invalid → evaluation_missing, rerun from evaluation_missing succeeds.
