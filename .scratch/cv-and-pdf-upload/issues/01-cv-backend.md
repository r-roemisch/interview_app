# 01 CV backend

Status: resolved
Blocked by: none

Store an optional CV on each Interview and give it to the interviewer according to Difficulty. See spec "CV" and "Who reads the CV", and `CONTEXT.md` (CV, Difficulty).

- `models.py`: `Interview.cv`, nullable text.
- `POST /interviews`: optional `cv`, max 20,000 characters, stripped; empty becomes null. `start_interview` takes it.
- "Practice again" copies the CV.
- `GET /cv/latest` → `{cv}`: the CV of the most recently created Interview that has one, else null. Declare the route so it cannot clash with `/interviews/{id}`.
- `InterviewOut` does not expose the CV.
- `prompts/interviewer.py`:
  - Easy: CV not in the prompt.
  - Normal: CV in a `<cv>` block, with the instruction that some Questions may draw on real experiences from it and most stay general.
  - Hard: CV in the prompt, with the instruction to probe its claims (specifics, numbers, what the candidate personally did).
  - The Closing uses the same system prompt, so the same rule applies.
- The Judge, Persona and Recommended Settings prompts never receive the CV.
- `create_all` does not add columns: delete the local SQLite file once, and extend the existing README note.

Done when tests cover: CV stored on creation and copied by practice again; `/cv/latest` returns the newest CV and null when none exist; interviewer prompt includes the CV for Normal and Hard only, and Hard includes the probe instruction; Judge, Persona and Recommended Settings prompts contain no CV.

## Comments

- 2026-09-28: Done. `Interview.cv` (nullable text); `POST /interviews` takes `cv` (max 20,000, stripped, blank becomes null); practice again copies it; `InterviewOut` does not expose it. `GET /cv/latest` lives in a new `routers/cv.py` under `/cv`, so it cannot clash with `/interviews/{id}`. `prompts/interviewer.py` adds a `<cv>` block with a Normal or Hard rule (`_CV_RULES`); Easy gets no CV. The Closing shares the system prompt. `tests/test_cv.py` adds 9 tests; 58 passed. Instead of deleting the local `interview.db`, the `cv` column was added with `ALTER TABLE`, so the existing History was kept. README note updated.
