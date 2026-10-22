from io import BytesIO

import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from entrevistador.domain.documents import MAX_FILE_BYTES, extract_document, validate_context

OFFER = "Ingeniero backend con Python, SQL y experiencia en diseño de APIs REST."


@pytest.mark.parametrize("filename", ["oferta.txt", "oferta.MD"])
def test_reads_utf8_with_bom(filename):
    assert extract_document(filename, OFFER.encode("utf-8-sig")) == OFFER


def test_reads_docx_paragraphs_and_tables():
    document = Document()
    document.add_paragraph("Oferta para ingeniería civil y gestión de proyectos.")
    document.add_table(rows=1, cols=1).cell(0, 0).text = "Requisito: cálculo estructural."
    output = BytesIO()
    document.save(output)
    text = extract_document("oferta.docx", output.getvalue())
    assert "ingeniería civil" in text
    assert "cálculo estructural" in text


def pdf_bytes(*, text=None, pages=1, encrypted=False):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=612, height=792)
        if text:
            font = DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                    NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
                }
            )
            page[NameObject("/Resources")] = DictionaryObject(
                {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
            )
            content = DecodedStreamObject()
            content.set_data(f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET".encode("cp1252"))
            page[NameObject("/Contents")] = content
    if encrypted:
        writer.encrypt("password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def test_reads_pdf_text():
    assert OFFER == extract_document("oferta.pdf", pdf_bytes(text=OFFER))


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (pdf_bytes(), "OCR"),
        (pdf_bytes(pages=41), "40 páginas"),
        (pdf_bytes(encrypted=True), "contraseña"),
    ],
)
def test_rejects_unusable_pdf(data, message):
    with pytest.raises(ValueError, match=message):
        extract_document("oferta.pdf", data)


@pytest.mark.parametrize(
    ("filename", "data", "message"),
    [
        ("a.txt", b"", "vacío"),
        ("a.txt", b"a" * (MAX_FILE_BYTES + 1), "5 MB"),
        ("a.txt", b"\xff", "UTF-8"),
        ("a.exe", b"test", "Formato"),
        ("a.docx", b"invalid", "dañado"),
        ("a.pdf", b"invalid", "dañado"),
        ("a.txt", b"short", "40 caracteres"),
        ("a.txt", b"a" * 20_001, "20,000"),
    ],
)
def test_rejects_invalid_documents(filename, data, message):
    with pytest.raises(ValueError, match=message):
        extract_document(filename, data)


def test_context_is_trimmed():
    assert validate_context(f"  {OFFER}\n") == OFFER
