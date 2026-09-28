# 16 UI rebuild

Status: resolved
Blocked by: 15

Apply prototype **C, Interview room** (issue 14, `frontend/app/prototype/c/`) to all four pages. See spec "UI". Use the prototype as the visual reference and keep it until this issue is done.

Why C: the Question tracker and STAR reminder help the candidate practise, which neither A nor B offers. B's always-visible History adds nothing during an Interview.

## Everywhere

- Accent colour: indigo, as in the prototypes. Neutrals: Tailwind zinc.
- Top bar from C (app name, New interview, History) replaces `nav.tsx`, keeping `BackendStatus` on the right.
- Rebuild the shared pieces in `app/ui.tsx` from `prototype/shared.tsx` (Persona avatar, composer, error notice with Retry, judging footer, End button). Still no component library; icons from `lucide-react`.
- The root layout's `max-w-3xl` `<main>` has to give way to full-height layouts where a page needs one (Interview page).
- Flows and URLs unchanged. Light/dark via system setting. Desktop first, mobile usable.

## Interview page

- C's layout: numbered Questions and grey Answer blocks in the centre, the Answer box pinned to the bottom, and a right panel with the Persona (initials, name, title), the Job (title, industry, Seniority, Difficulty), the 10-segment Question tracker, the STAR reminder and "End interview".
- The Closing is the indigo "Closing from <Persona>" block; after it, the judging footer with "See evaluation", or "Re-run evaluation" when the Evaluation is missing.
- Below `lg` the panel folds into C's strip (avatar + tracker) that expands to the full panel.
- The Persona comes from the API (issue 15).

## Other pages

- Setup, Evaluation and History use the top bar, colours, type and components above; no side panel.
- Evaluation: score card labelled Judge. Transcript in C's numbered style, Questions labelled with the Persona, STAR Breakdown under each Answer.
- History: no Persona on rows.

## Done when

All four pages use the new look in light and dark at 1440px and 390px, `tsc`, `eslint` and `next build` are clean, and `frontend/app/prototype/` is deleted.

## Comments

- 2026-09-28: User picked C after comparing A, B and C in the browser. Unblocked from 14.
- 2026-09-28: Done. Root layout is a full-height column (top bar + scrolling `<main>`); pages other than the Interview page use `<Page>` from `ui.tsx`. `ui.tsx` rebuilt (buttons, Page, ErrorBanner, Spinner, Field, StatusBadge, PersonaAvatar, StarLetter); Interview-only pieces (Panel, QuestionTracker, Composer, JudgingFooter) live in the Interview page. STAR hints moved to `lib/labels.ts`. Send stays enabled on an empty box (an empty Answer is still an Answer). Two existing bugs fixed on the Interview page: Retry after a failed "End interview" sent an answer instead of ending, and "Re-run evaluation" never restarted polling. Evaluation page order is now score card (Judge), improvement points, transcript. `app/prototype/` deleted. `tsc`, `eslint`, `next build` clean. Full flow driven in headless Chromium against `LLM_PROVIDER=fake` on a scratch DB, light and dark, 1440px and 390px; only console error was the deliberately aborted request for the error state.
