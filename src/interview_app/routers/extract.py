from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from interview_app.services.extract import MAX_PDF_BYTES, PdfTextError, check_upload, extract_text

router = APIRouter(tags=["setup"])


class ExtractedText(BaseModel):
    text: str


@router.post("/extract-text", response_model=ExtractedText)
def post_extract_text(file: UploadFile = File(...)) -> ExtractedText:
    # A plain `def` endpoint runs in a worker thread, so parsing a PDF does not block the server.
    # Read one byte past the limit so an oversized file is detected without reading all of it.
    data = file.file.read(MAX_PDF_BYTES + 1)
    try:
        check_upload(file.content_type, data)
        return ExtractedText(text=extract_text(data))
    except PdfTextError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
