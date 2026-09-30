# 04 Setup layout: settings on top, documents below (frontend)

Status: resolved
Blocked by: none

See spec "3. Setup layout".

- `frontend/app/page.tsx`: the order from the spec. Card "Interview settings" with the Job fields and all choices; a small "Optional documents" label; the Job description card (text box, Upload PDF, Recommend settings; hint says it fills Job title, Industry and Seniority above); the CV card; Start.
- After Recommend settings succeeds, scroll the "Interview settings" card into view (smooth).
- If 03 is not done yet, leave room for the Demeanor row under Difficulty; if it is, keep it there.

Done when tsc, lint and build pass and in the browser: the new order, Recommend fills the fields and scrolls up, Upload PDF still works for both documents.

## Comments
- 2026-09-30: Done. "Interview settings" card first, then "Optional documents" with the Job description and CV cards. Recommend settings scrolls the settings card back into view (checked: scrollTop 903 → 130, the fields filled). "Optional." dropped from both document hints, since the section label says it.
