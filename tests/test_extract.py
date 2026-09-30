import io

from pypdf import PdfWriter

from interview_app.services.extract import MAX_PDF_BYTES, MAX_PDF_PAGES, MAX_TEXT_CHARS


def _text_pdf(*pages: str) -> bytes:
    """A minimal valid PDF with one line of Helvetica text per page."""
    n = len(pages)
    font_id = 3 + 2 * n
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + b" ".join(b"%d 0 R" % (3 + 2 * i) for i in range(n)) + b"] /Count %d >>" % n,
    ]
    for i, text in enumerate(pages):
        stream = b"BT /F1 12 Tf 72 720 Td (" + text.encode() + b") Tj ET"
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents %d 0 R "
            b"/Resources << /Font << /F1 %d 0 R >> >> >>" % (4 + 2 * i, font_id)
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for num, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % num + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for off in offsets:
        out.write(b"%010d 00000 n \n" % off)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref))
    return out.getvalue()


def _blank_pdf() -> bytes:
    """What a scanned PDF looks like to pypdf: pages without a text layer."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _upload(client, data: bytes, content_type="application/pdf", name="file.pdf"):
    return client.post("/extract-text", files={"file": (name, data, content_type)})


def test_text_pdf_returns_its_text(client):
    r = _upload(client, _text_pdf("Senior Backend Engineer", "Python and PostgreSQL"))
    assert r.status_code == 200, r.text
    text = r.json()["text"]
    assert "Senior Backend Engineer" in text and "Python and PostgreSQL" in text
    assert text.index("Senior") < text.index("Python")


def test_octet_stream_is_accepted_when_the_file_is_a_pdf(client):
    r = _upload(client, _text_pdf("Hello"), content_type="application/octet-stream")
    assert r.status_code == 200, r.text


def test_pdf_without_text_is_rejected(client):
    r = _upload(client, _blank_pdf())
    assert r.status_code == 422
    assert r.json()["detail"] == "No text found in this PDF. Paste the text instead."


def test_non_pdf_is_rejected(client):
    r = _upload(client, b"just some text", content_type="text/plain", name="cv.txt")
    assert r.status_code == 422
    assert r.json()["detail"] == "Only PDF files can be uploaded."


def test_file_pretending_to_be_a_pdf_is_rejected(client):
    r = _upload(client, b"PK\x03\x04 a zip file")
    assert r.status_code == 422
    assert r.json()["detail"] == "Only PDF files can be uploaded."


def test_oversized_pdf_is_rejected(client):
    r = _upload(client, b"%PDF-1.4\n" + b"0" * MAX_PDF_BYTES)
    assert r.status_code == 422
    assert r.json()["detail"] == "The PDF is larger than 5 MB."


def test_corrupt_pdf_is_rejected(client):
    r = _upload(client, b"%PDF-1.4\nthis is not really a pdf")
    assert r.status_code == 422
    assert r.json()["detail"] == "This PDF could not be read. Paste the text instead."


def test_encrypted_pdf_is_rejected(client):
    writer = PdfWriter(clone_from=io.BytesIO(_text_pdf("Secret")))
    writer.encrypt(user_password="secret", algorithm="RC4-128")
    buf = io.BytesIO()
    writer.write(buf)
    r = _upload(client, buf.getvalue())
    assert r.status_code == 422
    assert r.json()["detail"] == "This PDF could not be read. Paste the text instead."



def test_short_pdf_is_not_truncated(client):
    assert _upload(client, _text_pdf("Senior Backend Engineer")).json()["truncated"] is False


def test_only_the_first_pages_are_read(client):
    pages = [f"Page {n}" for n in range(1, MAX_PDF_PAGES + 3)]
    body = _upload(client, _text_pdf(*pages)).json()
    assert f"Page {MAX_PDF_PAGES}" in body["text"] and f"Page {MAX_PDF_PAGES + 1}" not in body["text"]
    assert body["truncated"] is True


def test_long_text_is_cut_to_the_field_limit_at_a_line_break(client):
    # Each page is one 1,994-character line: ten pages end just below 20,000 characters, the 11th crosses it.
    pages = [f"P{n} " + "x" * 1990 for n in range(12)]
    body = _upload(client, _text_pdf(*pages)).json()
    assert body["truncated"] is True
    assert len(body["text"]) <= MAX_TEXT_CHARS
    assert body["text"].split("\n")[-1] == "P9 " + "x" * 1990  # cut at the page break, not mid-line
