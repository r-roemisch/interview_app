# The Judge is a separate prompt from the interviewer

The interviewer's prompt is tuned for a natural, Difficulty-dependent conversation. The Evaluation is produced by a second, independent LLM call (the Judge) that receives the Job and the full transcript and returns structured data validated with Pydantic. The alternative, asking the same conversation to score itself at the end, was rejected because the interviewer's role-play would bias the score and because a conversation prompt is a poor place to enforce a strict output schema.

## Consequences

- One extra LLM call per Interview, after the Closing.
- The Judge can be re-run on a Completed or Evaluation Missing Interview without touching the transcript.
- Judge prompts and interviewer prompts can be iterated independently and tested with a fake LLM client.
