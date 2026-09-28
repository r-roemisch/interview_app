# Judge choice (LLM Judge or JEV Judge): spec

Status: resolved
Confirmed by the user on 2026-09-28 after a grilling session. Build order: after `cv-and-pdf-upload`, before `voice-interview`. Vocabulary in `CONTEXT.md` (Judge, LLM Judge, JEV Judge, Checklist, Evaluation). Decision record: ADR-0003. Extends `.scratch/interview-practice/spec.md`.

## Purpose

Let the candidate choose which Judge scores an Interview, and compare the two Judges on the same transcript.

## Setup

- "Judge" is a required choice on Setup: **LLM Judge** (default) or **JEV Judge**. Stored on the Interview; not editable afterwards.
- Under the choice, a short "How the JEV Judge works" note (text below).
- "Practice again" copies the chosen Judge.

## The LLM Judge

Unchanged (ADR-0002): the existing prompt, output and retry rules.

## The JEV Judge

- One call to JEV (`typesafe/jev-1.13` on OpenRouter's `/api/v1/systemone` endpoint, plain HTTP with `httpx`, existing OpenRouter key). Pin the version: confidence values are only meaningful for one version.
- **State**: the Job snapshot and the full transcript with numbered Answers, in the same shape the LLM Judge receives. No CV, no Persona.
- **Questions** in one call:
  - For each Answer N, four `score` questions (Situation, Task, Action, Result of Answer N), each with 5 level descriptions matching 1-5 ("1 = absent or very weak" … "5 = excellent"). The rating is JEV's score rounded to the nearest level, plus 1.
  - One `score` question with 10 levels for the whole Interview, judged on STAR structure and fit to the Job. Overall Score = round(score / 9 × 100).
  - One `choice` question for the Verdict: strong_hire, hire, no_hire, each with a description.
  - One `noul` (yes/no) question per Checklist check, about the whole Interview.
- **Confidence**: JEV's confidence is stored for every rating, the Overall Score and the Verdict. For a Checklist check, the stored value is JEV's probability of "yes".
- **Improvement Points**: the three checks with the lowest probability of "yes", in that order, using each check's pre-written wording. This always gives exactly three, even if every check passes.
- **No text**: STAR comments and the justification are empty for a JEV Evaluation.
- **Failure**: 2 automatic retries for connection, timeout, rate-limit and server errors (same policy as `OpenRouterClient`), no retry for rejected requests. Missing or malformed answers count as a failure. On failure the Interview becomes Evaluation Missing, as with the LLM Judge.

### Checklist (draft; the user edits it at review)

| Check (asked as yes/no about the whole Interview) | Improvement Point when weakest |
|---|---|
| Results are quantified with numbers or clear outcomes | End every story with a measurable result: a number, a time saved, a before and after. |
| The candidate says "I" when describing their own actions | Say "I" for what you personally did, and keep the team's work separate. |
| The Situation and Task are set up briefly | Keep the Situation and Task to two sentences and spend your time on the Actions. |
| Answers address the Question that was asked | Answer the Question asked before adding anything else; restate it if it helps you focus. |
| Examples are specific real events, not hypotheticals | Use one specific real example instead of describing what you would usually do. |
| Answers include what was learned or would be done differently | Close with what you learned or what you would do differently next time. |
| Examples relate to the skills the Job needs | Pick examples that show the skills this Job asks for. |
| Answers are concise and structured | Keep answers under two minutes and follow Situation, Task, Action, Result in order. |

### "How the JEV Judge works" text (draft; same wording on Setup and on the Evaluation)

> The JEV Judge is a model that doesn't write text. It picks answers from fixed scales: a 1-5 rating for each part of every STAR answer, an overall score and a verdict, and it says how confident it is in each one. It doesn't explain its ratings. Your Improvement Points come from a fixed checklist of good interview habits: the three habits JEV was least sure you showed. For written feedback, choose the LLM Judge or run it afterwards to compare.

## Evaluation page

- Shows the chosen Judge's Evaluation, labelled with the Judge's name.
- A JEV Evaluation has the explanation box at the top and a legend for confidence markers. Each STAR rating, the Overall Score and the Verdict show a small confidence marker (high / medium / low, from the stored confidence; thresholds are display-only, e.g. ≥ 0.85 high, < 0.6 low).
- A "Run LLM Judge" / "Run JEV Judge" button runs the other Judge. It is synchronous: the button shows a spinner and the Evaluation appears when the request returns. An error shows next to the button with a retry and does not change the Interview's status.
- Once both Evaluations exist, a comparison section shows them side by side: the two Overall Scores, the two Verdicts, and per Answer the STAR ratings next to each other. The comparison stays; there is no remove button.
- "Re-run evaluation" (Evaluation Missing) re-runs the chosen Judge only.

## History

- Rows show a small "LLM" or "JEV" badge next to the Overall Score, for the chosen Judge. The score is the chosen Judge's.

## API

| Method | Path | Change |
|---|---|---|
| POST | `/interviews` | adds `judge`: `llm` \| `jev`, default `llm` |
| GET | `/interviews/{id}/evaluation` | unchanged meaning: the chosen Judge's Evaluation (404 while Judging, 409 if Evaluation Missing) |
| GET | `/interviews/{id}/evaluations` | all Evaluations of the Interview (0-2), each with its `judge` |
| POST | `/interviews/{id}/evaluations/{judge}` | runs the other Judge synchronously → 201 Evaluation; 409 if the Interview has not ended or `judge` is the chosen Judge; 503 if the Judge fails |
| POST | `/interviews/{id}/evaluation/rerun` | unchanged: re-runs the chosen Judge |
| GET | `/interviews` | History rows add `judge` |

`EvaluationOut` adds `judge`, makes `justification` and each STAR `comment` nullable, and adds nullable confidences (per STAR rating, `overall_confidence`, `verdict_confidence`) and `checklist` (list of `{check, probability}`, JEV only).

## Data model

- `interviews.judge`: `llm` / `jev`, default `llm`.
- `evaluations`: add `judge`; unique on (`interview_id`, `judge`) instead of `interview_id`; `justification` nullable; star breakdown JSON may hold `comment: null` and a `confidence` per rating; add `overall_confidence`, `verdict_confidence` (nullable floats) and `checklist` (nullable JSON).
- `Interview.evaluation` becomes the chosen Judge's Evaluation; the other is reached through the list.
- Delete the local SQLite file once; README note.

## Config

- `JEV_MODEL`, default `typesafe/jev-1.13`.
- `LLM_PROVIDER=fake` also fakes JEV with plausible scores, confidences and checklist probabilities.
- JEV works on the user's key without an allow-list change (checked 2026-09-29). When OpenRouter rejects a model because of the allow-list, the error message says which model and points to the allow-list.

## Tests

With a fake JEV client:
- Request built correctly: 4 questions per Answer, one Overall, one Verdict, one per Checklist check; state contains no CV and no Persona.
- Mapping: level to rating 1-5, 10-level score to 0-100, Verdict, the weakest three checks to Improvement Points in order, confidences stored.
- JEV failure → Evaluation Missing; rerun uses the chosen Judge.
- Other Judge: creates a second Evaluation, leaves status and History score unchanged; 409 for the chosen Judge; a failure returns 503 and leaves status unchanged.
- History row carries the chosen Judge.

## Out of scope

Automatic escalation from JEV to the LLM Judge, calibrating confidence thresholds, an LLM writing text for JEV, more than two Judges, removing a comparison.
