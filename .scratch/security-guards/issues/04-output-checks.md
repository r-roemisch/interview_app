# 04 Output checks: interviewer reply, Judge lengths, JEV ranges (backend)

Status: ready-for-agent
Blocked by: 01

See spec "B1", "B2", "B3", "Tests".

- `services/interview.py`: a reply check for Questions and the Closing (over 600 characters, or containing a rule line of 30+ characters or one of our tags); one more try; then a fixed fallback Question not yet asked (short list, e.g. in `prompts/interviewer.py`) or a fixed Closing; a warning in the log.
- `prompts/judge.py`: `max_length` on `comment` (300), `justification` (1,500), each Improvement Point (300).
- `services/jev_judge.py` (or `jev.py`): confidences and probabilities outside 0-1 make the answer unusable.
- Tests as in the spec (B1-B3).

Done when the B tests pass and the whole suite is green.

## Comments
