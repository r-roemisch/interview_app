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
PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}


class PdfTextError(Exception):
    """The upload cannot be turned into text. The message is shown to the user as is."""


def check_upload(content_type: str | None, data: bytes) -> None:
    if len(data) > MAX_PDF_BYTES:
        raise PdfTextError("The PDF is larger than 5 MB.")
    # The header is the real check; some browsers send octet-stream for local files.
    if (content_type and content_type not in PDF_CONTENT_TYPES) or not data.startswith(b"%PDF"):
        raise PdfTextError("Only PDF files can be uploaded.")


def extract_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        # Many PDFs are "encrypted" with an empty password and open normally; others cannot be read.
        if reader.is_encrypted and not reader.decrypt(""):
            raise PdfTextError("This PDF could not be read. Paste the text instead.")
        pages = [page.extract_text() or "" for page in reader.pages]
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
    return text
