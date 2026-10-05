# 05 Setup choices and History label (frontend)

Status: resolved
Blocked by: 01, 04

See spec sections "Setup", "History" and "Guard 2: Daily Budget".

- `frontend/lib/labels.ts`: the four Interviewer Models (id, label, advantage) and the six Prompt Styles (value, label, description) from the spec.
- Setup (`frontend/app/page.tsx`): an "Interviewer model" dropdown (GPT-4.1 Mini selected; each option shows its advantage) and a "Prompt style" dropdown (Zero-shot selected) with the selected style's description under it. Send both with `POST /interviews`. A 429 shows its message like other start errors.
- History (`frontend/app/history/page.tsx`): small text on each row, e.g. "GPT-4.1 Mini · Few-shot".
- `frontend/lib/api.ts`: both fields on the create payload, on Interview and on History rows.

Done when, with `LLM_PROVIDER=fake`, an Interview with a non-default model and Prompt Style shows both in History, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-10-05: Done. `lib/api.ts`: `InterviewerModel`, `PromptStyle`, both fields on Interview, the create payload and History rows. `lib/labels.ts`: `INTERVIEWER_MODEL_OPTIONS`, `PROMPT_STYLE_OPTIONS`, `experimentLabel`. Setup: two dropdowns side by side after the Judge choice, each with the selected option's hint under it (dropdowns, not cards: six styles would crowd the page). History: "GPT-4.1 Mini · Few-shot" next to the status badge. A 429 shows through the existing error banner. tsc, lint, build pass; headless Chromium with `LLM_PROVIDER=fake`: non-default model and style stored and shown in History.
