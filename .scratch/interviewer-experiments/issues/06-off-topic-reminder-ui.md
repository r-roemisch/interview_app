# 06 Off-topic reminder on the Interview page (frontend)

Status: resolved
Blocked by: 03

See spec section "Guard 1: Off-topic Answers".

- Interview page (`frontend/app/interviews/[id]/page.tsx`): when an Answer is sent and the returned `off_topic_count` went up while the Interview is still In Progress, show an amber note under the open Question: strike 1 and strike 2 texts from the spec. The text stays in the Answer box so it can be edited. The note is not spoken in a Voice Interview and goes away on the next accepted Answer or a reload.
- Strike 3 needs nothing new: the page shows the Closing and the evaluation link as for any ended Interview.
- `frontend/lib/api.ts`: `off_topic_count` on Interview.

Done when, with a fake check scripted to say off-topic (e.g. a test-only switch in `DevFakeLLMClient` for an Answer containing "off-topic test"), the two reminders and the early end show in the browser, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-10-05: Done. `OFF_TOPIC_REMINDERS` in `lib/labels.ts`; `off_topic_count` on Interview. Interview page: `send()` compares the count before and after; an off-topic Answer shows the amber note (shield icon) after the open Question and puts the text back in the box. The note is page state only, so a reload or the next accepted Answer clears it, and it is never spoken (no new interviewer message). Headless Chromium with the fake provider: reminder 1, reminder 2 (replacing 1), the Answer text kept in the box, then the third ends the Interview with the fixed Closing and Evaluation. tsc, lint, build pass.
  Note for the user: the Evaluation page labels the fixed Closing "Closing from <Persona>", like every Closing.
