# 01 Interviewer Model and Prompt Style fields (backend)

Status: resolved

Each Interview stores an Interviewer Model and a Prompt Style; the interviewer's Questions and Closing use the chosen model. See spec sections "Setup", "LLM client", "API", "Data model". Vocabulary: Interviewer Model, Prompt Style in `CONTEXT.md`. The prompt itself does not change here: every Prompt Style still builds today's prompt until issue 02.

- `models.py`: `PromptStyle` enum (the six values); the four Interviewer Model ids as one constant; `Interview.interviewer_model` (default `openai/gpt-4.1-mini`), `Interview.prompt_style` (default `zero_shot`).
- `llm.py`: optional `model` on `LLMClient.complete` and `OpenRouterClient.complete`; `FakeLLMClient` records it; `DevFakeLLMClient` accepts and ignores it.
- `services/interview.py`: `_interviewer_says` passes the Interview's model. Persona creation does not.
- `POST /interviews` takes both fields and rejects other values (422). Practice again copies both. `InterviewOut` and `HistoryRow` carry both.
- Add both columns to the local SQLite file, keeping the History; README note (agent section).

Done when tests cover: Questions and Closing use the chosen model while the Persona and the Judge do not; 422 for an unknown model or Prompt Style; Practice again copies both; History rows carry both; existing tests pass. Then one real Interview of two Questions with each of the four models. If a model rejects the mid-conversation system messages, fix it in the client and note it here.

## Comments

- 2026-10-05: Done. `models.py`: `INTERVIEWER_MODELS`, `DEFAULT_INTERVIEWER_MODEL`, `PromptStyle`, `Interview.interviewer_model`, `Interview.prompt_style`. `llm.py`: `complete(..., model=None)` on the Protocol, `OpenRouterClient` (also names the model in retries/errors), `FakeLLMClient` (records it), `DevFakeLLMClient`. `_interviewer_says` passes the Interviewer Model; Persona and Judges do not. `InterviewCreate` validates the model with a `Literal` of the four ids. `InterviewOut`, `HistoryRow`, Practice again carry both. `tests/test_interviewer_model.py` (5 tests). Local `interview.db` backed up and the columns added with ALTER TABLE (all five Interviews kept). Real run, two Questions each, all four models accept the mid-conversation system messages, no client change needed: GPT-4.1 Mini ~1 s per Question, Claude Sonnet 5.5 ~2.5 s, Gemma 4 31B ~2.5 s, GPT-5 Nano ~10 s (it reasons by default; not tuned, per spec).
