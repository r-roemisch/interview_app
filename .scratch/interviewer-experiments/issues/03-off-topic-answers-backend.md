# 03 Off-topic Answers (backend)

Status: resolved
Blocked by: 01

Guard 1. See spec section "Guard 1: Off-topic Answers" and the answers and rerun rows in "API". Vocabulary: Off-topic Answer, Flagged Answer in `CONTEXT.md`.

- `config.py` and `.env.example`: `OFF_TOPIC_MODEL`, default `openai/gpt-5-nano`.
- A prompt module (e.g. `prompts/off_topic.py`): the open Question and the Answer inside `<answer>` (cleaned with `untrusted`), the definition and the three examples from the spec, JSON `{"off_topic": bool}`.
- `services/interview.py` `submit_answer`: check a non-empty Answer before storing it, with `model=OFF_TOPIC_MODEL`. Off-topic: do not store the Answer, add one to `off_topic_count`; on the third, store the fixed Closing, set `ended_early`, and either trigger the Judge or, with no Answers, set Evaluation Missing. A failed check counts as on-topic and logs a warning.
- `models.py`: `Interview.off_topic_count` (integer, default 0); `InterviewOut` carries it.
- `POST /interviews/{id}/evaluation/rerun`: 409 "There are no answers to evaluate." when the Interview has no Answers.
- `DevFakeLLMClient`: answers the check with `{"off_topic": false}`.
- Add the column to the local SQLite file; README note.

Done when tests cover: strikes 1 and 2 store nothing but the count and leave the Question open; strike 3 ends early with the fixed Closing and runs the Judge; strike 3 with no real Answers gives Evaluation Missing and rerun gives 409; an empty Answer makes no check call; a failed check or unusable JSON counts as on-topic; the check uses `OFF_TOPIC_MODEL` and gets no CV or Job Description. Then a real check of the three spec examples with GPT-5 Nano, noted in a comment.

## Comments

- 2026-10-05: Done. `prompts/off_topic.py` (definition, the three spec examples, JSON schema), `services/off_topic.py`: `LLMOffTopicCheck` (any failure → on-topic, logged), `FakeOffTopicCheck`, dependency `get_off_topic_check`. `submit_answer` takes `off_topic=`; `_off_topic_answer` counts the strike and, on the third (`OFF_TOPIC_LIMIT`), stores `OFF_TOPIC_CLOSING`, sets `ended_early` and Judging, or Evaluation Missing without Answers. Rerun gives 409 "There are no answers to evaluate." `Interview.off_topic_count` in `InterviewOut`. Conftest overrides the check with an always-on-topic fake. `DevFakeLLMClient`: off-topic only for an Answer containing "off-topic test" (for issue 06). `tests/test_off_topic.py` (6 tests).
  Real check with GPT-5 Nano on six Answers (the three spec examples, a weak Answer, a translation request, a good STAR Answer): 6/6 right, 2 to 8 s each. With `reasoning: minimal` it took ~1 s but marked the Judge example and the weak Answer off-topic; GPT-4.1 Nano made the same mistakes. Kept GPT-5 Nano at default reasoning: a false strike is worse than the wait. README says so.
