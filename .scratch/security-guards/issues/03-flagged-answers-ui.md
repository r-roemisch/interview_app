# 03 Flagged Answers on the Evaluation page (frontend)

Status: resolved
Blocked by: 02

See spec "A3" (Evaluation page).

- `frontend/app/interviews/[id]/evaluation/page.tsx`: a Flagged Answer's STAR row shows an amber note "This Answer contained instructions to the Judge, so it was scored as no answer." Works for both Judges and in the comparison table (a flag per Judge).
- No "injection" wording anywhere in the UI.

Done when tsc, lint, build pass and a Flagged Answer shows the note in the browser (fake backend with a scripted Evaluation, or a test row in a throwaway database).

## Comments
- 2026-09-30: Done. An amber note with a warning icon above a Flagged Answer's STAR rows; its comments are hidden since they only repeat the note; "· flagged" in the Judges comparison table. Checked in the browser with the fake backend and a throwaway database (flag set on a stored Evaluation). tsc, lint, build pass.
