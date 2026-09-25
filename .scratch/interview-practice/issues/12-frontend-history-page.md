# 12 History page

Status: resolved
Blocked by: 07, 08

Page `/history`: table of rows (title, date, status badge, Overall Score). Row click: Completed → evaluation page, In Progress → interview page, Evaluation Missing → evaluation page (which shows Re-run). Delete button per row with a confirm dialog.

Done when all three statuses route correctly and delete removes the row.

## Comments

- 2026-09-25: Done. `app/history/page.tsx`: table with title, date, StatusBadge, score; row click routes in_progress → chat, everything else → evaluation page; Delete per row with confirm and stopPropagation. Verified: `tsc`, `eslint`, `next build` clean; full flow driven through `lib/api.ts` from Node against the backend in `LLM_PROVIDER=fake` mode (recommend → 10 answers → closing → evaluation → early end → rerun → practice again → history → delete); every route returns 200 server-side. No browser on this machine, so the interactive UI itself is unverified.
