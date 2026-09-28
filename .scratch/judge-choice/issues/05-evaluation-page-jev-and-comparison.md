# 05 Evaluation page: JEV Evaluation and comparison (frontend)

Status: resolved
Blocked by: 03, 04

See spec "Evaluation page".

- Label the Evaluation with its Judge's name.
- JEV Evaluation:
  - The explanation box at the top, using the shared text from issue 04, with a legend for confidence markers.
  - A high / medium / low confidence marker next to each STAR rating, the Overall Score and the Verdict (≥ 0.85 high, < 0.6 low; display only).
  - No empty comment or justification placeholders: hide those parts.
  - Improvement Points displayed as usual.
- A "Run LLM Judge" / "Run JEV Judge" button for the Judge that was not chosen. Spinner while the request runs (the LLM Judge can take tens of seconds). On error, a message and a retry next to the button.
- When both Evaluations exist (from `GET /interviews/{id}/evaluations`), a comparison section: both Overall Scores and Verdicts side by side, and per Answer both sets of STAR ratings next to each other. No remove button.
- "Re-run evaluation" on Evaluation Missing is unchanged (chosen Judge).
- `frontend/lib/api.ts`: `listEvaluations`, `runJudge`, and the new `EvaluationOut` fields.
- README agent section: describe the Judge choice and the comparison.

Done when a manual run with `LLM_PROVIDER=fake` shows a JEV Evaluation with markers and explanation, running the LLM Judge adds the comparison, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-09-29: Done, all in `app/interviews/[id]/evaluation/page.tsx`. The score card names the Judge; for JEV its right column shows the shared `JEV_EXPLANATION` and a legend instead of the missing justification. `Confidence` is a coloured dot (green high, amber medium, red low via `confidenceLevel` in `lib/labels.ts`) with the exact value on hover, next to the Overall Score, the Verdict and each STAR rating. Empty STAR comments are not rendered. `RunOtherJudge` waits for `POST /evaluations/{judge}` with a spinner and shows errors next to the button, which retries. `Comparison` is a small table: Overall score, Verdict, and per Answer "S3 T3 A4 R3" for both Judges. The page loads `GET /evaluations` with the Evaluation, so the comparison survives a reload. No re-run button for the other Judge once compared (not needed). README agent section: a short note on the Judges. tsc, lint, build pass; headless Chromium with `LLM_PROVIDER=fake`: JEV Evaluation with dots and explanation, running the LLM Judge adds the comparison, and it is still there after reload.
