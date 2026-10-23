"""Pull text out of a PDF or a photo of a page."""

import io

import pytesseract
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.textutil import clean_text

MAX_OCR_WIDTH = 2000


class UnsupportedFileError(Exception):
    """The upload is not a PDF or an image we can read."""


class ExtractionError(Exception):
    """The file looked valid but no text could be read from it."""


def detect_kind(filename: str, content_type: str, data: bytes) -> str:
    """Prefer file magic over the name. Phones sometimes send a generic type."""
    name = (filename or "").lower()
    media = (content_type or "").split(";")[0].strip().lower()
    if data.startswith(b"%PDF"):
        return "pdf"
    if _looks_like_image(data):
        return "image"
    if media == "application/pdf" or name.endswith(".pdf"):
        return "pdf"
    if media.startswith("image/") or _image_extension(name):
        return "image"
    raise UnsupportedFileError("Upload a PDF or an image (PNG, JPEG, WEBP, or GIF).")


def extract_text(filename: str, content_type: str, data: bytes) -> str:
    if not data:
        raise ExtractionError("The file is empty.")
    kind = detect_kind(filename, content_type, data)
    if kind == "pdf":
        text = _extract_pdf(data)
    else:
        text = _extract_image(data)
    text = clean_text(text)
    if not text:
        raise ExtractionError(
            "No text could be read from this file. "
            "Try a text-based PDF, or a sharper photo of the page."
        )
    return text


def _extract_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
    except PdfReadError as exc:
        raise ExtractionError("This PDF could not be opened. It may be damaged.") from exc
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def _extract_image(data: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(data))
        image.seek(0)
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ExtractionError("This image could not be opened.") from exc
    if image.width > MAX_OCR_WIDTH:
        ratio = MAX_OCR_WIDTH / image.width
        resized = (MAX_OCR_WIDTH, max(1, int(image.height * ratio)))
        image = image.resize(resized, Image.Resampling.LANCZOS)
    try:
        return pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    except pytesseract.TesseractNotFoundError as exc:
        raise ExtractionError(
            "OCR is unavailable because Tesseract is not installed on the API host."
        ) from exc


def _looks_like_image(data: bytes) -> bool:
    png = data.startswith(b"\x89PNG\r\n\x1a\n")
    jpeg = data.startswith(b"\xff\xd8\xff")
    gif = data.startswith(b"GIF8")
    if png or jpeg or gif:
        return True
    return len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP"


def _image_extension(name: str) -> bool:
    return name.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
