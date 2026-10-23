import io
from pathlib import Path

from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
]


def pdf_bytes(text: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 7, text)
    return bytes(pdf.output())


def png_bytes(text: str, *, font_size: int = 64) -> bytes:
    font_path = next((path for path in FONT_CANDIDATES if path.exists()), None)
    if font_path is None:
        raise FileNotFoundError("DejaVuSans.ttf is not installed")
    font = ImageFont.truetype(str(font_path), font_size)
    image = Image.new("RGB", (1800, 360), "white")
    draw = ImageDraw.Draw(image)
    draw.text((48, 120), text, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
