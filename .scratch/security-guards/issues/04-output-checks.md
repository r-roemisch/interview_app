# 04 Output checks: interviewer reply, Judge lengths, JEV ranges (backend)

Status: resolved
Blocked by: 01

See spec "B1", "B2", "B3", "Tests".

- `services/interview.py`: a reply check for Questions and the Closing (over 600 characters, or containing a rule line of 30+ characters or one of our tags); one more try; then a fixed fallback Question not yet asked (short list, e.g. in `prompts/interviewer.py`) or a fixed Closing; a warning in the log.
- `prompts/judge.py`: `max_length` on `comment` (300), `justification` (1,500), each Improvement Point (300).
- `services/jev_judge.py` (or `jev.py`): confidences and probabilities outside 0-1 make the answer unusable.
- Tests as in the spec (B1-B3).

Done when the B tests pass and the whole suite is green.

## Comments
- 2026-09-30: Done. `prompts/interviewer.py`: rules and closing instructions moved to constants, `reply_problem` (over 600 characters, one of our tags, or any instruction sentence of 30+ characters; quoted examples like "That doesn't sound like much." are allowed), `fallback_question` (ten neutral Questions, the first with a greeting), `FALLBACK_CLOSING`. `services/interview.py` `_interviewer_says` for every Question and Closing. Judge caps 300/1,500/300. JEV `_unit` check on every confidence and probability. `tests/test_output_guards.py` 18 tests; 171 passed.
