# Rude interviewer and Setup layout: spec

Status: resolved
Confirmed by the user on 2026-09-30 after a grilling session. Vocabulary in `CONTEXT.md` (Demeanor, Difficulty, Persona, Portrait, Judge, Recommended Settings).

## Purpose

Three adjustments the user asked for together:

1. The Setup page shows two scrollbars on the right, which makes it hard to navigate.
2. The candidate can practise against a rude interviewer, and the Portrait shows it.
3. The top of the Setup page is confusing: the settings to choose go on top, the documents to paste or upload below.

## 1. Double scrollbar

Only on the Setup page (`/`), at every window size: `<html>` scrolls and `<main>` scrolls inside it. Cause: the hidden inputs (`sr-only`, which is `position: absolute`) have no positioned ancestor, so they are placed against the page, not `<main>`; the lowest one (the CV's Upload PDF input) makes the page taller than the window. Found with Playwright on 2026-09-30; History, Interview and Evaluation pages have one scrollbar.

- Fix: `relative` on `<main>` in `frontend/app/layout.tsx`. Checked in the browser: the extra scrollbar goes away.
- The Interview page's left side panel may scroll on its own on short windows; that stays.

## 2. Demeanor

### Setting

- `Demeanor`: `friendly` (default) or `rude`. Chosen at Setup, independent of Difficulty: every Difficulty works with both.
- Stored on the Interview. Practice again copies it (and gets a new Persona and Portrait, as today).
- Recommended Settings never suggest it.

### Interviewer

- Friendly: the interviewer prompt stays exactly as today.
- Rude: the interviewer prompt adds a Demeanor rule. The interviewer is impatient, curt, openly sceptical and mildly sarcastic ("Fine. Next.", "That doesn't sound like much."), may cut a long answer short. Never insults, never swears, never remarks on the candidate as a person (appearance, background, accent, etc.). Hostile but professional.
- It holds from the greeting through every Question to the Closing. The Closing still gives no feedback and no Verdict.
- Difficulty rules are unchanged: a Rude Easy interviewer still asks no follow-ups.

### Not affected

- **Voice**: the speech sounds as today; rudeness is in the words only.
- **Persona**: the Persona call does not get the Demeanor. A rude interviewer has the same kind of name, title and voice as a friendly one.
- **Judges**: neither the LLM Judge nor the JEV Judge sees the Demeanor (ADR-0002: the interviewer's style must not bias the score). Overall Scores stay comparable across Demeanors.

### Portrait

- Friendly: as today (head and shoulders, friendly and professional expression).
- Rude: still photorealistic, framed as head and upper body; stern, unimpressed expression, arms crossed, leaning back slightly. Same background, light and "no text, no logos, no watermark".
- Without a Portrait (switched off, failed): initials, as today; nothing else shows the Demeanor there.

### Where it shows

- Interview page details panel and Evaluation page header: next to Difficulty, e.g. "Hard difficulty · Rude". Only when Rude; Friendly Interviews look as today.
- Not in History.

### Storage

- A new `demeanor` column on `interviews`. There are no migrations (README): delete `interview.db` once and restart, as with the Persona, CV, Judge choice and Voice Interviews. This also deletes the local History.

## 3. Setup layout

Top to bottom:

1. Card **"Interview settings"**: Job title, Industry, Seniority, Written/Voice, the Portrait switch, Difficulty, **Demeanor** (a choice-card row under Difficulty: "Friendly: patient and polite" / "Rude: impatient, sceptical, curt"), Judge.
2. A small label **"Optional documents"**.
3. Card **Job description**: text box, Upload PDF, Recommend settings. Hint: it fills Job title, Industry and Seniority above.
4. Card **Your CV**: text box, Upload PDF, the existing hint.
5. Start button.

- Recommend settings still overwrites Job title, Industry and Seniority (the user can edit them afterwards). After it succeeds, the page scrolls up to the "Interview settings" card so the change is seen.
- The page intro "Only the title is required" stays.

## API

| Method | Path | Change |
|---|---|---|
| POST | `/interviews` | adds `demeanor`: `friendly` \| `rude`, default `friendly` |
| POST | `/interviews/{id}/practice-again` | copies `demeanor` |
| GET | `/interviews/{id}` | `InterviewOut` adds `demeanor` |

`HistoryRow` does not change.

## Tests

Backend:
- `POST /interviews` without `demeanor` → `friendly`; with `rude` → `rude` in `InterviewOut`.
- Interviewer system prompt: the Rude rule is present for `rude` on Easy, Normal and Hard, absent for `friendly`; the Friendly prompt equals today's. The Closing messages carry the Rude rule too.
- Portrait prompt: crossed arms / stern expression for `rude`, the friendly expression for `friendly`.
- Persona messages, LLM Judge messages and JEV Judge input never mention the Demeanor.
- Practice again copies `demeanor`.

Frontend: tsc, lint and build pass; checked in the browser: one scrollbar on `/`, the new order, Recommend scrolls up, the Demeanor label on the Interview and Evaluation pages.

## Out of scope

More Demeanors than two, a rude speaking voice, rudeness in the Persona, the Judge scoring composure, showing the Demeanor in History, migrations.
