# 02 PDF text extraction endpoint

Status: resolved
Blocked by: none

`POST /extract-text` turns an uploaded PDF into text for the Job Description or CV box. See spec "PDF upload".

- Add `pypdf` and `python-multipart` with `uv add`.
- New router (e.g. `routers/extract.py`) plus a small service function that takes bytes and returns text, so it can be tested without HTTP.
- Multipart field `file`. Return 422 with a clear `detail` for each case:
  - not a PDF (content type and the `%PDF` header): "Only PDF files can be uploaded."
  - larger than 5 MB: "The PDF is larger than 5 MB."
  - no text after trimming (scanned or empty): "No text found in this PDF. Paste the text instead."
  - pypdf cannot read it (corrupt, encrypted): "This PDF could not be read. Paste the text instead."
- Join pages with blank lines and collapse runs of more than two newlines. No OCR, no layout mode.
- Nothing is written to disk.

Done when tests cover: a text PDF generated in the test (e.g. with pypdf, or a tiny fixture in `tests/fixtures/`) returns its text; a PDF with no text, a non-PDF, an oversized file and a corrupt PDF each return 422 with their message.

## Comments

- 2026-09-28: Done. `services/extract.py` (`check_upload`, `extract_text`, `PdfTextError` whose message goes to the user as is) and `routers/extract.py` (`POST /extract-text`, a plain `def` endpoint so parsing runs in a worker thread; reads at most 5 MB + 1 byte). Content type may be `application/pdf`, `application/x-pdf` or `application/octet-stream`; the `%PDF` header is the real check. Plain `pypdf` without the crypto extra, to keep dependencies small (user: "do not bloat the app"): AES-encrypted PDFs, even ones with an empty password, get "could not be read" and the user pastes the text. `tests/test_extract.py` builds its PDFs in code (no fixture files), 8 tests; 66 passed.
