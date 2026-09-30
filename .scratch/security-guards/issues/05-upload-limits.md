# 05 Upload limits: long PDFs, audio check, speech only for Voice (backend + frontend)

Status: resolved
Blocked by: none

See spec "C1 + C2", "C3", "C4", "Tests".

- `services/extract.py`: first 30 pages only; text cut at 20,000 characters (at a line break near the end if there is one); returns whether it was cut.
- `routers/extract.py`: `ExtractedText.truncated: bool`.
- `frontend/app/page.tsx` + `lib/api.ts`: the notice "The PDF was longer than we can use; only the first part was kept." under the Job description or CV field, gone when that text is edited or replaced.
- `routers/speech.py`: magic-byte check on `/transcriptions` (WAV `RIFF….WAVE`, MP3 `ID3` or frame sync, matching the declared type); speech 404 unless `voice_interview`.
- Tests as in the spec (C1-C4). README agent section: the PDF limits.

Done when the C tests pass, the suite is green, tsc/lint/build pass, and the notice shows in the browser for a long PDF.

## Comments
- 2026-09-30: Done. `MAX_PDF_PAGES = 30`, `MAX_TEXT_CHARS = 20_000`, cut at a line break within the last 500 characters; `ExtractedText.truncated`; the amber notice under the Job description or CV, cleared on edit. WAV/MP3 first-byte check on `/transcriptions`; speech 404 for written Interviews. Tests in `test_extract.py` (3) and `test_speech.py` (updated to real headers, 5 new). Checked in the browser: a 12-page PDF kept 19,948 characters and showed the notice. README agent section: a "Guards" paragraph.
