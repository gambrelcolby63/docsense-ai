import pytesseract
import pytest
from app.services.extraction import ExtractionError, UnsupportedFileError, extract_text
from tests.helpers import png_bytes


def test_image_ocr_reads_a_clear_page():
    image = png_bytes("The parcel token is purple kite 42.")
    text = extract_text("page.png", "image/png", image).lower()
    assert "purple" in text
    assert "42" in text


def test_png_magic_wins_over_a_misleading_name():
    image = png_bytes("Door code 4419")
    text = extract_text("notes.pdf", "application/pdf", image)
    assert "4419" in text


def test_missing_tesseract_explains_itself(monkeypatch):
    def explode(*args, **kwargs):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr("app.services.extraction.pytesseract.image_to_string", explode)
    image = png_bytes("Hello")
    with pytest.raises(ExtractionError, match="Tesseract"):
        extract_text("page.png", "image/png", image)


def test_plain_text_is_rejected():
    with pytest.raises(UnsupportedFileError):
        extract_text("notes.txt", "text/plain", b"hello")


def test_corrupt_pdf_is_rejected():
    with pytest.raises(ExtractionError):
        extract_text("bad.pdf", "application/pdf", b"%PDF-1.7 this is not a real pdf")
