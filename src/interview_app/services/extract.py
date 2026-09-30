"""PDF upload: turn a Job Description or CV PDF into text for a Setup box (spec: PDF upload).

Only the text is returned; the file is never stored. No OCR, so scanned PDFs have no text.
"""

from __future__ import annotations

import io
import logging
import re

from pypdf import PdfReader

log = logging.getLogger(__name__)

MAX_PDF_BYTES = 5 * 1024 * 1024
# Longer PDFs are read in part (spec: security-guards C1, C2): the pages that fit, and the text up
# to the CV and Job Description field limit, so a long PDF can no longer make Start fail.
MAX_PDF_PAGES = 30
MAX_TEXT_CHARS = 20_000
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}


class PdfTextError(Exception):
    """The upload cannot be turned into text. The message is shown to the user as is."""


def check_upload(content_type: str | None, data: bytes) -> None:
    if len(data) > MAX_PDF_BYTES:
        raise PdfTextError("The PDF is larger than 5 MB.")
    # The header is the real check; some browsers send octet-stream for local files.
    if (content_type and content_type not in PDF_CONTENT_TYPES) or not data.startswith(b"%PDF"):
        raise PdfTextError("Only PDF files can be uploaded.")


def extract_text(data: bytes) -> tuple[str, bool]:
    """The PDF's text, and whether it was cut to fit."""
    try:
        reader = PdfReader(io.BytesIO(data))
        # Many PDFs are "encrypted" with an empty password and open normally; others cannot be read.
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfTextError("This PDF could not be read. Paste the text instead.")
        truncated = len(reader.pages) > MAX_PDF_PAGES
        pages = [page.extract_text() or "" for page in reader.pages[:MAX_PDF_PAGES]]
    except PdfTextError:
        raise
    except Exception as exc:  # pypdf raises many different errors for broken files
        log.warning("PDF could not be read: %s", exc)
        raise PdfTextError("This PDF could not be read. Paste the text instead.") from exc

    text = "\n\n".join(p.strip() for p in pages)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise PdfTextError("No text found in this PDF. Paste the text instead.")
    if len(text) > MAX_TEXT_CHARS:
        text, truncated = _cut(text), True
    return text, truncated


def _cut(text: str) -> str:
    """Cut at the last line break near the limit, so the kept text does not end mid-sentence."""
    head = text[:MAX_TEXT_CHARS]
    line_break = head.rfind("\n")
    return (head[:line_break] if line_break > MAX_TEXT_CHARS - 500 else head).rstrip()
