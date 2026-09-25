# 09 Setup page

Status: resolved
Blocked by: 06, 08

Page `/`: form with title (required), industry, seniority select (default mid), job description textarea, difficulty select (default normal). "Recommend settings" button, enabled when the description is non-empty, calls `/recommend-settings` and fills title/industry/seniority; the user can still edit them. "Start interview" posts to `/interviews` and navigates to `/interviews/[id]`. Show inline errors for 503.

Done when a full setup→start flow works against the running backend.

## Comments

- 2026-09-25: Done. `app/page.tsx`: form with title (required), industry, seniority (default mid), job description, difficulty radio cards with hints; Recommend settings fills title/industry/seniority and stays editable; Start posts and navigates; 503/502 shown in an ErrorBanner. Shared `app/ui.tsx` (Button, LinkButton, ErrorBanner, Spinner, Field, StatusBadge) and `lib/labels.ts`. Verified: `tsc`, `eslint`, `next build` clean; full flow driven through `lib/api.ts` from Node against the backend in `LLM_PROVIDER=fake` mode (recommend → 10 answers → closing → evaluation → early end → rerun → practice again → history → delete); every route returns 200 server-side. No browser on this machine, so the interactive UI itself is unverified.
