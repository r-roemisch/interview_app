# 02 Flagged Answers (backend)

Status: ready-for-agent
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
