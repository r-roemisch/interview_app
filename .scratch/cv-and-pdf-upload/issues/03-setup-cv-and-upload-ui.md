# 03 Setup page: CV box and PDF upload

Status: resolved
Blocked by: 01, 02

Frontend for the CV and the PDF uploads on the Setup page (`frontend/app/page.tsx`). See spec "PDF upload" and "CV". Same visual language as the rest of Setup (issue 16 of interview-practice); icons from `lucide-react`.

- A CV text box below the Job fields, optional, with a character counter against 20,000. On page load, pre-fill it from `GET /cv/latest`; the candidate can clear it.
- An "Upload PDF" button next to the Job Description box and next to the CV box. It opens a file picker limited to `.pdf`, posts to `/extract-text`, shows a spinner, and on success replaces the box's text. On error, shows the API's `detail` under the box; the existing text stays.
- After a Job Description is filled from a PDF, the Recommended Settings flow behaves exactly as after pasting.
- Send `cv` with `POST /interviews`. "Practice again" needs no frontend change (the backend copies it).
- `frontend/lib/api.ts`: `extractText(file)`, `latestCv()`, and `cv` on the create payload.
- README agent section: mention CV and PDF upload, and the new dependencies.

Done when a manual run with `LLM_PROVIDER=fake` shows: uploading a text PDF fills the box, a scanned PDF shows the "No text found" message, the CV is pre-filled on the next visit to Setup, and `npm run lint` and `npm run build` pass.

## Comments

- 2026-09-28: Done, kept small (user: "do not bloat the app"). `app/page.tsx`: CV textarea after Difficulty with `maxLength={20000}` instead of a character counter; pre-filled once from `GET /cv/latest`. A local `PdfUpload` component (a `<label>` around a hidden file input) is used next to "Recommend settings" and under the CV box; it replaces the box's text on success. Upload errors go to the page's existing error banner rather than under each box. `lib/api.ts`: `cv` on create, `latestCv()`, `extractText(file)`; `request()` no longer forces a JSON Content-Type for FormData bodies. README agent section: pypdf in Stack, extraction in layout. Checked with lint, tsc and build, and in headless Chromium against `LLM_PROVIDER=fake`: a text PDF fills the Job Description box, a blank PDF shows "No text found", the CV is sent and pre-filled on the next visit.
