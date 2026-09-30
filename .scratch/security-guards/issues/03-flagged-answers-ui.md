# 03 Flagged Answers on the Evaluation page (frontend)

Status: ready-for-agent
Blocked by: 02

See spec "A3" (Evaluation page).

- `frontend/app/interviews/[id]/evaluation/page.tsx`: a Flagged Answer's STAR row shows an amber note "This Answer contained instructions to the Judge, so it was scored as no answer." Works for both Judges and in the comparison table (a flag per Judge).
- No "injection" wording anywhere in the UI.

Done when tsc, lint, build pass and a Flagged Answer shows the note in the browser (fake backend with a scripted Evaluation, or a test row in a throwaway database).

## Comments
