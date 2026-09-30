# 03 Demeanor in the UI (frontend)

Status: resolved
Blocked by: 02

See spec "2. Demeanor" ("Where it shows") and "3. Setup layout" (where the row goes).

- `lib/api.ts`: `Demeanor` type; `demeanor` on the create payload and `InterviewOut`.
- `lib/labels.ts`: `DEMEANOR_OPTIONS` (Friendly: "Patient and polite", Rude: "Impatient, sceptical, curt").
- Setup page: a `ChoiceCards` row "Demeanor" directly under Difficulty, default Friendly, sent with the create request.
- Interview page details panel and Evaluation header: "· Rude" next to the Difficulty, only when Rude.

Done when tsc, lint and build pass and a Rude Interview shows the label on both pages in the browser.

## Comments
- 2026-09-30: Done. `Demeanor` in `lib/api.ts`, `DEMEANOR_OPTIONS` in `lib/labels.ts`, a Demeanor row under Difficulty on Setup, "Normal · Rude" in the Interview panel, a "Rude interviewer" chip on the Evaluation header. Checked in the browser with `LLM_PROVIDER=fake` and a throwaway database.
