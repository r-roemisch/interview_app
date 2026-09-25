# 10 Interview page

Status: resolved
Blocked by: 04, 05, 08

Page `/interviews/[id]`: loads the Interview, renders the transcript as a chat (interviewer left, candidate right), a counter "Question n of 10", a textarea + Send, and an "End interview" button enabled after the first Answer. On Send: post the Answer, append the returned Question or Closing. On a Closing: hide the input, show "See evaluation" disabled, poll `/interviews/[id]/evaluation` every 2 s; enable the button on 200, turn it into "Re-run evaluation" on 409 (which calls rerun and resumes polling). On 503 from Send: keep the typed text, show an error and a Retry button. Works for resumed In Progress Interviews.

Done when a full 10-question run and an early-end run both reach the Evaluation page.

## Comments

- 2026-09-25: Done. `app/interviews/[id]/page.tsx`: loads via `useParams`, chat bubbles (answer right, closing amber), 'Question n of 10', textarea + Send (Ctrl+Enter), End interview enabled after first Answer with confirm; failed Send keeps the draft and shows Retry; after Closing polls `/evaluation` every 2 s, See evaluation enables on 200, Re-run shown on 409. Works for resumed Interviews. Lint rule `react-hooks/set-state-in-effect` (React compiler) forced in-effect fetches with a cancel flag and a `reloadKey` counter instead of a `load()` callback. Verified: `tsc`, `eslint`, `next build` clean; full flow driven through `lib/api.ts` from Node against the backend in `LLM_PROVIDER=fake` mode (recommend → 10 answers → closing → evaluation → early end → rerun → practice again → history → delete); every route returns 200 server-side. No browser on this machine, so the interactive UI itself is unverified.
