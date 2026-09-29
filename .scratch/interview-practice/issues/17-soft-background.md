# 17 Soft page background (frontend)

Status: resolved

The plain white background felt too bright and flat: cards were barely grey on white and blended into the page. Decided after a grilling session on 2026-09-29: one background for every page, a cool tint with a gentle gradient, static, with a dark version; white cards with soft shadows; the top bar and the Interview side panel slightly see-through.

- `globals.css`: page tint `#f5f6fb` with a faint indigo radial glow at the top; dark `#0b0d14` with a matching glow. The body fills the window and `<main>` scrolls, so the background stays put.
- `ui.tsx`: `cardClass` (white, light border, soft shadow) and `glassClass` (translucent with blur), used on all pages. In dark mode surfaces are slightly translucent so the blue tint shows through.
- Secondary text `zinc-500` became `zinc-600` / dark `zinc-400`: on the tint it fell below 4.5:1 (3.7:1 under the glow). The Answer box hint went from `zinc-400` to the same.

## Log

- 2026-09-29: Three variants were prototyped on every page with a switcher: 1 top glow, 2 indigo and violet corner glows, 3 flat cool tint. The user picked **1 (top glow)**. The full prototype is on the branch `prototype/background-variants` (commit e497c9b), not on the main line. Folded in: variant 1 only, switcher removed. tsc, lint, build pass.
