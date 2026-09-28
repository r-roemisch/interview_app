# 04 Setup Judge choice and History badge (frontend)

Status: resolved
Blocked by: 02

See spec "Setup" and "History".

- Setup (`frontend/app/page.tsx`): a required "Judge" choice, LLM Judge selected by default, styled like the Difficulty choice. Under it, the "How the JEV Judge works" text from the spec (keep the wording in one shared constant, e.g. in `frontend/lib/labels.ts`, because issue 05 shows it too). Send `judge` with `POST /interviews`.
- History (`frontend/app/history/page.tsx`): a small "LLM" or "JEV" badge next to the Overall Score.
- `frontend/lib/api.ts`: `judge` on the create payload and on History rows.

Done when a manual run with `LLM_PROVIDER=fake` creates a JEV Interview whose History row shows the JEV badge, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-09-29: Done. `lib/labels.ts`: `JUDGE_OPTIONS`, `JUDGE_LABEL`, `JEV_EXPLANATION` (shared with issue 05). Setup: the Difficulty cards became a small generic `ChoiceCards` component in `app/page.tsx`, reused for the Judge choice (LLM Judge default), so no card markup is duplicated; the "How the JEV Judge works" note shows under the choice while JEV is selected. History: the label under the score reads "LLM score" or "JEV score" instead of a separate badge. `lib/api.ts`: `Judge` type on Interview, create payload and History rows. tsc, lint, build pass; headless Chromium with `LLM_PROVIDER=fake`: choosing JEV shows the note, the Interview is stored with `judge: jev`, History shows "JEV score".
