# 02 Portrait on Setup, Interview and Evaluation (frontend)

Status: resolved
Blocked by: 01

See spec "Setup", "Generation" and "Where it shows".

- `lib/api.ts`: `portrait` on `InterviewCreate` and `Interview`, and the Portrait URL.
- Setup: the switch "Show a portrait of the interviewer (about 4 cents)", on by default, next to the Written/Voice choice.
- A Persona face component: the Portrait when ready, initials with a loading shimmer while pending, initials otherwise. Sizes for the panel (rounded square, full panel width) and small (strip, Evaluation).
- Interview page: side panel on the left with the large Portrait at its top, name and title under it. While the Portrait is pending, poll every 2 s and update only the Portrait state, so a poll can never overwrite a newer transcript. The Portrait fades in.
- Folded strip below `lg` and the Evaluation page: the small Portrait in place of the initials.
- The interview-practice spec: drop "Interviewer pictures" and "image generation" from out of scope, and mention the Portrait where the Persona's initials are described.

Done when tsc, lint and build pass and the page is checked in a browser with `LLM_PROVIDER=fake` (pending shimmer, then the Portrait) and once with the real model.

## Comments

- 2026-09-29: Done. `lib/api.ts`: `PortraitState`, `portrait` on `Interview` and `InterviewCreate`, `portraitUrl`. `PersonaAvatar` (ui.tsx) shows the Portrait when ready (fading in over the initials), pulsing initials while pending, initials otherwise; new size `panel`. Setup: checkbox "Show a portrait of the interviewer (about 4 cents)", on by default, under the Written/Voice choice. Interview page: side panel on the left, large Portrait with name and title under it; polls every 2 s while pending and takes only the Portrait state from the reply. Folded strip and Evaluation page: small Portrait. Interview-practice spec updated. tsc, lint, build pass.
- Browser, `LLM_PROVIDER=fake`: switch on by default; pulsing initials first, then the placeholder; switched off, no image and no polling. Browser, real models: Interview open after 2.5 s, Portrait (Olivia Parker, Senior Product Designer) shown after 12 s, small Portrait on the Evaluation page.
