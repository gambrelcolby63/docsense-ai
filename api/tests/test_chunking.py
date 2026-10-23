from app.services.chunking import chunk_text
from app.services.textutil import clean_text


def test_empty_text_has_no_chunks():
    assert chunk_text("  \n\n  ") == []


def test_short_paragraphs_pack_together():
    text = "Alpha sentence is short.\n\nBeta sentence is also short."
    assert chunk_text(text, size=200, overlap=20) == [text]


def test_long_paragraph_keeps_overlap_on_word_boundaries():
    paragraph = "word " * 400
    chunks = chunk_text(paragraph, size=120, overlap=30)
    assert len(chunks) > 2
    assert all(token == "word" for chunk in chunks for token in chunk.split())
    tail = chunks[0].split()[-3:]
    assert all(word in chunks[1].split() for word in tail)


def test_pdf_line_wraps_rejoin_into_sentences():
    raw = (
        "The cutoff is 16:00 local time\n"
        "on weekdays. Drivers wait.\n"
        "The lead is Mina Solberg."
    )
    cleaned = clean_text(raw)
    assert "time on weekdays" in cleaned
    assert "Mina Solberg." in cleaned


def test_separate_paragraphs_stay_apart_when_they_do_not_fit():
    first = "A" * 80
    second = "B" * 80
    chunks = chunk_text(f"{first}\n\n{second}", size=100, overlap=10)
    assert chunks == [first, second]
