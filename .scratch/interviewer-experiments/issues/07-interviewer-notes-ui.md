# 07 Interviewer's Notes on the Evaluation page (frontend)

Status: resolved
Blocked by: 02

See spec section "Interviewer's Notes". Vocabulary: Interviewer's Notes in `CONTEXT.md`.

- Evaluation page (`frontend/app/interviews/[id]/evaluation/page.tsx`): fetch `GET /interviews/{id}/notes`; when there is a plan or any notes, a collapsed "Interviewer's notes" section: the plan first, then each Question or Closing that has notes, its text followed by its notes. Hidden when there are none.
- `frontend/lib/api.ts`: the notes call and type.

Done when, with `LLM_PROVIDER=fake`, a Plan-ahead and a Chain-of-thought Interview show their notes, a Zero-shot one shows no section, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-10-05: Done. `api.getNotes` and `InterviewerNotes`. Evaluation page: `NotesSection`, a collapsed `<details>` card above the footer, shown in every state once the Interview has ended (also while Judging or Evaluation Missing), hidden when there are no notes or they cannot be loaded. Plan first, then each Question/Closing text with its notes. Headless Chromium with the fake provider: Chain-of-thought and Plan-ahead show their notes, Zero-shot shows no section. tsc, lint, build pass.
