from app.services.embeddings import cosine, local_embed


def test_similar_texts_are_closer_than_unrelated_texts():
    query, related, unrelated = local_embed(
        [
            "oslo depot warehouse code",
            "the oslo depot warehouse code is fjord 1842",
            "banana bread recipe with cinnamon",
        ]
    )
    assert cosine(query, related) > cosine(query, unrelated)
    assert cosine(query, related) > 0.2


def test_embeddings_are_deterministic_and_normalized():
    first = local_embed(["Mina Solberg covers the Nordic region"])
    second = local_embed(["Mina Solberg covers the Nordic region"])
    assert first == second
    norm = sum(value * value for value in first[0]) ** 0.5
    assert abs(norm - 1) < 1e-6


def test_empty_text_is_a_zero_vector():
    vector = local_embed(["..."])[0]
    assert all(value == 0 for value in vector)
