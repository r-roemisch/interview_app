# 02 Flagged Answers (backend)

Status: resolved
Blocked by: 01

See spec "A3", "Tests"; `CONTEXT.md` (Flagged Answer).

- `prompts/judge.py`: `JudgeAnswerAssessment.flagged: bool`, described in the prompt.
- `prompts/jev_judge.py`: `answer{n}_flagged` yes/no question per Answer; `services/jev_judge.py` flags at ≥ 0.7.
- `services/judge.py` and `services/jev_judge.py`: for a Flagged Answer, all four ratings become 1; the LLM Judge's comments become "Contained instructions to the Judge." Overall Score, Verdict, Improvement Points untouched.
- `schemas.StarBreakdown.flagged: bool = False` (stored in the `star_breakdowns` JSON; no column, no database deletion).
- `frontend/lib/api.ts`: `flagged` on the STAR breakdown type.
- Tests as in the spec (A3).

Done when the A3 tests pass and the whole suite is green.

## Comments
- 2026-09-30: Done. `JudgeAnswerAssessment.flagged` (default false, so a reply without it is still valid); `answer{n}_flagged` yes/no for JEV, flagged at ≥ 0.7 (`FLAG_THRESHOLD`); both services set a Flagged Answer's four ratings to 1 (LLM comments "Contained instructions to the Judge.", JEV confidences None). `StarBreakdown.flagged = False`, stored in the JSON, no column. The dev fake JEV never flags. `tests/test_flagged_answers.py` 7 tests.
