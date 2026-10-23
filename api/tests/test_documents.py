from tests.helpers import pdf_bytes

OSLO = (
    "The Oslo depot warehouse code is Fjord-1842. "
    + "Northwind ships wool blankets from the Oslo depot on weekdays. " * 25
)
MINA = (
    "The on-call lead for the Nordic region is Mina Solberg. "
    + "Mina Solberg covers night calls for the Nordic region. " * 25
)
NOTES = f"{OSLO}\n\n{MINA}"


def _upload(client, name: str, data: bytes, content_type: str):
    return client.post(
        "/api/documents",
        files={"file": (name, data, content_type)},
    )


def test_upload_summary_chat_history_and_delete(client):
    created = _upload(client, "notes.pdf", pdf_bytes(NOTES), "application/pdf")
    assert created.status_code == 201, created.text
    document = created.json()
    assert document["provider"] == "mock"
    assert document["embedding_provider"] == "local"
    assert document["chunk_count"] >= 2
    assert "Fjord-1842" in document["extracted_text"]
    assert "Mina Solberg" in document["extracted_text"]
    assert document["summary"]
    assert document["key_points"]
    assert "Fjord-1842" in document["summary"] or any(
        "Fjord-1842" in point for point in document["key_points"]
    )

    listing = client.get("/api/documents")
    assert listing.status_code == 200
    ids = [item["id"] for item in listing.json()]
    assert document["id"] in ids
    assert "extracted_text" not in listing.json()[0]

    detail = client.get(f"/api/documents/{document['id']}")
    assert detail.status_code == 200
    assert "Mina Solberg" in detail.json()["extracted_text"]

    answer = client.post(
        f"/api/documents/{document['id']}/chat",
        json={"question": "Who is the on-call lead for the Nordic region?"},
    )
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert "Mina Solberg" in body["answer"]
    assert body["citations"]
    assert "Mina Solberg" in body["citations"][0]["text"]
    assert body["citations"][0]["score"] > 0
    assert "Fjord-1842" not in body["citations"][0]["text"]

    missing = client.post(
        f"/api/documents/{document['id']}/chat",
        json={"question": "Who baked the banana bread?"},
    )
    assert missing.status_code == 200
    assert "couldn't find" in missing.json()["answer"].lower()

    history = client.get(f"/api/documents/{document['id']}/messages")
    assert history.status_code == 200
    messages = history.json()
    assert [item["role"] for item in messages] == ["user", "assistant", "user", "assistant"]
    assert messages[1]["citations"]

    removed = client.delete(f"/api/documents/{document['id']}")
    assert removed.status_code == 204
    assert removed.content == b""
    assert client.get(f"/api/documents/{document['id']}").status_code == 404
    assert client.post(
        f"/api/documents/{document['id']}/chat",
        json={"question": "Who is Mina?"},
    ).status_code == 404


def test_blank_pdf_and_unsupported_file_and_oversize(client):
    blank = _upload(client, "blank.pdf", pdf_bytes(""), "application/pdf")
    # An empty cell still produces a PDF. Extraction should refuse it.
    assert blank.status_code == 422

    rejected = _upload(client, "notes.txt", b"just words", "text/plain")
    assert rejected.status_code == 415

    client.app.state.settings.max_upload_bytes = 32
    oversized = _upload(client, "big.pdf", b"%PDF" + b"0" * 64, "application/pdf")
    assert oversized.status_code == 413

    missing = client.post("/api/documents/does-not-exist/chat", json={"question": "Hi"})
    assert missing.status_code == 404

    blank_question = client.post(
        "/api/documents/does-not-exist/chat",
        json={"question": "   "},
    )
    # The document is missing, so this is a 404 before the blank check if we look up first.
    # A real document with a blank question is covered below.
    assert blank_question.status_code == 404


def test_blank_question_is_rejected(client):
    created = _upload(
        client,
        "notes.pdf",
        pdf_bytes("The warehouse code for the Oslo depot is Fjord-1842."),
        "application/pdf",
    )
    assert created.status_code == 201, created.text
    response = client.post(
        f"/api/documents/{created.json()['id']}/chat",
        json={"question": "   "},
    )
    assert response.status_code == 422


def test_documents_are_listed_newest_first(client, tmp_path):
    first = _upload(
        client,
        "one.pdf",
        pdf_bytes("The first memo says the crate count is 10 units exactly."),
        "application/pdf",
    )
    second = _upload(
        client,
        "two.pdf",
        pdf_bytes("The second memo says the crate count is 80 units exactly."),
        "application/pdf",
    )
    assert first.status_code == 201
    assert second.status_code == 201
    # Force an older timestamp so the order does not depend on the clock.
    import sqlite3

    connection = sqlite3.connect(tmp_path / "test.db")
    connection.execute(
        "update documents set created_at = ? where id = ?",
        ("2020-01-01 00:00:00", first.json()["id"]),
    )
    connection.commit()
    connection.close()
    listing = client.get("/api/documents").json()
    assert [item["id"] for item in listing[:2]] == [second.json()["id"], first.json()["id"]]
