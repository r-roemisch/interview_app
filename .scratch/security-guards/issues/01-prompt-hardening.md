# 01 Prompt hardening: untrusted text is data (backend)

Status: ready-for-agent
Blocked by: none

See spec "A1", "A2", "Tests"; `CONTEXT.md` (CV, Job Description, Answer).

- One helper (e.g. `prompts/untrusted.py`) that removes our tag names from untrusted text, and for Answers also the fake transcript labels.
- `prompts/interviewer.py`: CV and Job Description introduced as material, never instructions; rule that instructions inside the candidate's messages are never followed; title, industry, CV, JD, Answers passed through the helper.
- `prompts/recommend.py`: the same for the Job Description.
- `prompts/judge.py`: `transcript_block` puts each Answer in `<answer n="…">`; `job_block` wraps the JD in `<job_description>`; the LLM Judge prompt says `<answer>` content is the candidate's words, never instructions. JEV reuses both blocks.
- Tests as in the spec (A1/A2). Existing tests that match on `CANDIDATE (answer n): …` are updated to the new shape.

Done when the A1/A2 tests pass and the whole suite is green.

## Comments
