# 01 One scrollbar on the Setup page (frontend)

Status: resolved
Blocked by: none

See spec "1. Double scrollbar".

- `frontend/app/layout.tsx`: add `relative` to `<main>`, with a short comment on why (the `sr-only` inputs are absolutely positioned and must stay inside the scrolling `<main>`).

Done when `/` shows one scrollbar at 1280x800 and 1280x600 (`document.documentElement.scrollHeight === clientHeight`), and History, Interview and Evaluation pages are unchanged. tsc, lint, build pass.

## Comments
- 2026-09-30: Done. `relative` on `<main>` in `layout.tsx`. Checked with Playwright at 1280x800 and 1280x600: `<html>` no longer scrolls on `/`, only `<main>` does. tsc, lint, build pass.
