# 11 Evaluation page

Status: resolved
Blocked by: 07, 08

Page `/interviews/[id]/evaluation`: header with Overall Score, Verdict and justification; then the transcript with each STAR Breakdown (S/T/A/R 1-5 with comments) rendered directly under its Question and Answer; then the three Improvement Points; then "Practice again" (calls practice-again and navigates to the new Interview) and a link to History. If the Interview is Evaluation Missing, show a Re-run button instead of the content.

Done when the page renders a real Evaluation and Practice again starts a new Interview.

## Comments

- 2026-09-25: Done. `app/interviews/[id]/evaluation/page.tsx`: score/verdict/justification header, transcript with a STAR star-table under each Answer (keyed by message position), three improvement points, Practice again (navigates to the new Interview), Back to history. Redirects to the chat if the Interview is still in progress; polls while judging; Re-run button when Evaluation Missing. Verified: `tsc`, `eslint`, `next build` clean; full flow driven through `lib/api.ts` from Node against the backend in `LLM_PROVIDER=fake` mode (recommend → 10 answers → closing → evaluation → early end → rerun → practice again → history → delete); every route returns 200 server-side. No browser on this machine, so the interactive UI itself is unverified.
