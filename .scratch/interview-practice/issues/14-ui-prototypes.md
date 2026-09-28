# 14 UI prototypes

Status: resolved
Blocked by: none

Three throwaway visual prototypes of the Interview page so the user can pick a layout by looking. See spec "UI".

- A **Focused chat**: slim top bar, one centred column, full-height messages, Answer box pinned to the bottom, thin progress bar ("3 / 10") under the header.
- B **Sidebar app**: permanent left sidebar with "New interview" and a History list, chat on the right.
- C **Interview room**: chat in the centre, right panel with Job, Seniority, Difficulty, a 10-dot Question tracker and a short STAR reminder.

Rules:

- Everything lives in `frontend/app/prototype/`: `a/`, `b/`, `c/`, a shared `fake-data.ts`, and an index page at `/prototype` linking all three.
- Each page renders as a full-screen overlay (`fixed inset-0`) so the real nav and layout are hidden. No real file is edited and no real file imports from `prototype/`.
- Each page has a loud fixed banner, e.g. `PROTOTYPE B · Sidebar app`, with links to the other two.
- Same accent colour (indigo) in all three: the comparison is layout only.
- Fake Persona ("Priya Nair, Head of Customer Success") shown with initials in a circle.
- A state switcher on each page: In Progress, interviewer thinking, error + Retry, Closing + Judging.
- Works in light and dark (system setting). Desktop first; on a phone the sidebar/panel collapses and the Answer box still works.
- Add `lucide-react` to `frontend/package.json` (it stays for issue 16).
- Never commit the `prototype/` folder. Removal is `rm -rf frontend/app/prototype`.

Done when `/prototype/a`, `/b`, `/c` render all four states, `tsc` and `eslint` are clean, and `git status` shows no modified real frontend files besides `package.json` / `package-lock.json`.

## Comments

- 2026-09-28: Done. `frontend/app/prototype/` (untracked): `page.tsx` index, `a/`, `b/`, `c/`, `fake-data.ts`, `shared.tsx` (banner, state switcher, Persona avatar, composer, error notice, judging footer, End button). `lucide-react` added. `tsc` and `eslint` clean. All three pages screenshotted in all four states, light and dark, at 1440px and 390px with a headless Chromium; the only console errors come from the real nav's backend-status check behind the overlay (backend not running). Waiting on the user's pick for issue 16.
