# 04 Interview flow API and interviewer prompt

Status: resolved
Blocked by: 02, 03

`prompts/interviewer.py`: system prompt built from Job snapshot and Difficulty using the definitions in `CONTEXT.md`. Instructs: behavioral questions, one question per message, greeting only on the first message, follow-ups allowed per Difficulty, seniority mid if unspecified, ground questions in Job Description when present.

`services/interview.py` + `routers/interviews.py`:
- `POST /interviews`: persist Interview (status in_progress), call LLM for greeting+first Question, persist as message position 0, return `InterviewOut`.
- `POST /interviews/{id}/answers`: reject if not in_progress. Persist Answer, then if question_count < 10 call LLM for next Question, else call LLM for Closing (prompt: list finished) and set status to a pending-evaluation state that the Judge issue will resolve. On `LLMUnavailable` roll back the Answer so state is unchanged; return 503.
- `POST /interviews/{id}/end`: requires ≥1 Answer; LLM Closing with "candidate ended early" instruction; set `ended_early`.
- `GET /interviews/{id}`.

Done when tests with `FakeLLMClient` cover: full 10-question run, early end, LLM failure leaves no partial Answer, answering a non-in_progress Interview is rejected.

## Comments

- 2026-09-25: Done. `prompts/interviewer.py` (system prompt from Job snapshot + Difficulty rules, transcript mapping, next-question and closing message builders), `services/interview.py` (`start_interview`, `submit_answer`, `end_interview`; rollback on LLM failure; `on_closing` hook), `routers/interviews.py` (POST /interviews, GET /interviews/{id}, POST .../answers, POST .../end; 404/409/422/503 mapping), `services/judge.py` stub with `run_judge_in_background` for issue 05 to fill. Enum columns switched to SQLAlchemy `Enum(native_enum=False)` so loaded rows yield enums. 11 flow tests with the fake LLM.
