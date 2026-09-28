# CV and PDF upload: spec

Status: ready-for-agent
Confirmed by the user on 2026-09-28 after a grilling session. Build order: this feature first, then `judge-choice`, then `voice-interview`. Vocabulary in `CONTEXT.md` (CV, Job Description, Difficulty). Extends `.scratch/interview-practice/spec.md`.

## Purpose

Make Interviews more personal. The candidate can add their CV, and can upload the Job Description and CV as PDFs instead of pasting them.

## PDF upload

- A PDF is only a way to fill a text box. Setup has an "Upload PDF" button next to the Job Description box and next to the CV box.
- The backend extracts the text with `pypdf` (BSD licence) and returns it. The frontend puts it into the box, replacing what was there, and the candidate can edit it before starting. For the Job Description, the existing Recommended Settings flow runs on the text exactly as if it had been pasted.
- The file is never stored. Only the text the candidate submits with the Interview is kept.
- No OCR. If the PDF has no text layer (a scan) or the extracted text is empty after trimming, return an error and show "No text found in this PDF. Paste the text instead."
- Limits: PDF only (checked by content type and the `%PDF` header), 5 MB max. Clear error messages for each.
- Multi-column CVs may come out with lines interleaved. Accepted: the candidate can fix the text on Setup.

## CV

- Optional free text on Setup, below the Job fields. Max 20,000 characters (same kind of limit as Answers).
- Stored on the Interview as a snapshot, like the Job. "Practice again" copies it.
- Setup pre-fills the CV box with the CV of the most recently created Interview that has one. The candidate can clear or replace it.
- Not shown after Setup: the CV is not part of the Interview page or the Evaluation.

## Who reads the CV

- The interviewer only, depending on Difficulty (definitions in `CONTEXT.md`):
  - Easy: the CV is not given to the interviewer prompt at all.
  - Normal: the prompt receives the CV and may ground some Questions in experiences from it; most Questions stay general.
  - Hard: the prompt receives the CV and is told to probe its claims ("Your CV says you cut costs by 30%, walk me through how").
- Never the Judge (ADR-0002: judge only what the candidate said), never Recommended Settings (Seniority belongs to the Job), never the Persona call.
- Closing prompt: same rule as Questions (it may reference CV items discussed).

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/extract-text` | multipart `file` (PDF) → `{text}`; 422 with a message for not-a-PDF, too large, or no text found |
| GET | `/cv/latest` | `{cv: string \| null}` from the most recent Interview with a CV |
| POST | `/interviews` | adds optional `cv` |

`InterviewOut` does not include the CV (nothing after Setup shows it). `python-multipart` becomes a dependency for the upload.

## Data model

- `interviews.cv`: text, nullable.
- `create_all` does not add columns: delete the local SQLite file once; README note, as for the Persona.

## Tests

Backend with pytest, no frontend tests:
- Extraction: a small text PDF returns its text; an image-only or empty PDF returns 422 "no text"; a non-PDF and an oversized file return 422.
- CV stored on creation, copied by practice again, returned by `/cv/latest`.
- Interviewer prompt: contains the CV for Normal and Hard, not for Easy; Hard includes the probe instruction.
- Judge, Persona and Recommended Settings prompts never contain the CV.

## Out of scope

OCR, storing PDFs, a reusable "My CV" profile, CV in the Judge, parsing the CV into structured fields.
