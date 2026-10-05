# 02 Six Prompt Styles and the Interviewer's Notes (backend)

Status: resolved
Blocked by: 01

The Prompt Style changes the interviewer's prompt; Chain-of-thought, Plan-ahead and Self-check leave Interviewer's Notes. See spec sections "Prompt Styles", "Cleaning a reply", "Interviewer's Notes", "Fake provider", and the notes row in "API".

- `prompts/interviewer.py`:
  - `build_system_prompt` adds the block for the Interview's Prompt Style; Zero-shot stays exactly today's prompt. Example replies in double quotes.
  - A plan prompt for Plan-ahead, and the `<plan>` block in the system prompt when the Interview has a plan.
  - A function that splits a reply into message and notes by Prompt Style and reports a malformed reply.
  - The new tags join `_TAGS`; the new instructions join `_instruction_sentences`.
- `services/interview.py`: `_interviewer_says` returns the message and its notes; the reply check runs on the message; a malformed reply counts as bad. `start_interview` makes the plan call (Interviewer Model) for Plan-ahead, after the Persona; a failed plan call logs a warning and starts without a plan.
- `models.py`: `Interview.plan` (nullable text), `Message.notes` (nullable text); notes cut at 4,000 characters, plan at 1,500.
- `GET /interviews/{id}/notes`: `{plan, messages: [{message_id, notes}]}`, 409 while In Progress.
- `llm.py` `DevFakeLLMClient`: a fixed plan; tags for Chain-of-thought and Self-check when the prompt asks for them.
- Add the two columns to the local SQLite file; README note.

Done when tests cover: each Prompt Style builds the right prompt and Zero-shot matches today's; One-shot has only its Difficulty's example; the message is stored without tags and the notes are stored; an empty message, unclosed `<thinking>` or missing `<final>` is retried, then falls back without notes; the plan is stored and in every Question's prompt; a failed plan call starts without one; a leftover tag or a repeated new instruction is flagged, a message close to an example reply is not; notes give 409 while In Progress. Then one real Interview per Prompt Style with GPT-4.1 Mini, noted in a comment.

## Comments

- 2026-10-05: Done. `prompts/interviewer.py`: example block (One-shot: the Difficulty's example; Few-shot: all three), Chain-of-thought and Self-check rules, plan prompt and `<plan>` block, `split_reply` (message + notes), new tags in `_TAGS`, new instructions in `_instruction_sentences`; `reply_problem` now also rejects an empty message. `services/interview.py`: `_interviewer_says` returns (message, notes); `create_plan` for Plan-ahead. `Interview.plan`, `Message.notes`; `GET /interviews/{id}/notes` (409 while In Progress). `DevFakeLLMClient` writes a plan and tagged replies. `tests/test_prompt_styles.py` (19 tests).
  Real runs with GPT-4.1 Mini, two Questions per style, all six usable. Two prompt changes came out of them (spec updated): (1) GPT-4.1 Mini skipped the thinking and copied the Self-check draft without a check, because the transcript shows earlier Questions without tags; the Self-check rule now says every reply has three parts "even though your earlier messages show only the last one", and the check is one yes/no line per question. (2) Claude Sonnet 5.5 returned nothing (`finish_reason: content_filter`) for Chain-of-thought whenever the prompt said `<thinking>`, "step by step" or "your earlier messages show none" (3/3 each); with a short `<assessment>` and none of those words it answers 3/3, and GPT-4.1 Mini still writes the assessment every time. Chain-of-thought and Self-check also checked on GPT-5 Nano, Claude Sonnet 5.5 and Gemma 4 31B.
