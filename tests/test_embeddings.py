
from uuid import uuid4

import pytest

from app.embeddings import add_text, search_text


def test_add_text_and_search():
    text_id = f"test-{uuid4()}"
    text = "Finish the project report by Friday"

    add_text(text=text, text_id=text_id)

    results = search_text(
        "Finish the project report by Friday",
    )

    assert any(
        result["id"] == text_id
        and result["text"] == text
        and result["distance"] <= 0.5
        for result in results
    )


def test_search_filters_results_above_threshold(monkeypatch):
    from app import embeddings

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        lambda **kwargs: {
            "ids": [["close-match", "distant-match"]],
            "documents": [["Relevant text", "Unrelated text"]],
            "distances": [[0.2, 0.5]],
        },
    )

    results = search_text("some query")

    assert len(results) == 2
    assert results[0]["id"] == "close-match"
    assert results[1]["id"] == "distant-match"


def test_search_returns_empty_when_no_result_meets_threshold(monkeypatch):
    from app import embeddings

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        lambda **kwargs: {
            "ids": [["distant-match"]],
            "documents": [["Unrelated text"]],
            "distances": [[0.8]],
        },
    )

    results = search_text("some query")

    assert results == []


def test_search_returns_empty_when_collection_has_no_matches(monkeypatch):
    from app import embeddings

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        lambda **kwargs: {
            "ids": [[]],
            "documents": [[]],
            "distances": [[]],
        },
    )

    assert search_text("some query") == []


def test_search_uses_cosine_distance(monkeypatch):
    from app import embeddings

    original_query = embeddings.collection.query
    captured = {}

    def fake_query(**kwargs):
        captured.update(kwargs)
        return {
            "ids": [[]],
            "documents": [[]],
            "distances": [[]],
        }

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        fake_query,
    )

    search_text("test query")

    assert captured["include"] == ["documents", "distances"]
    assert captured["n_results"] == 5

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        original_query,
    )


def test_search_sorts_best_matches_first(monkeypatch):
    from app import embeddings

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        lambda **kwargs: {
            "ids": [["match-1", "match-2", "match-3"]],
            "documents": [["Text 1", "Text 2", "Text 3"]],
            "distances": [[0.4, 0.1, 0.3]],
        },
    )

    results = search_text("test query")

    assert [result["id"] for result in results] == [
        "match-2",
        "match-3",
        "match-1",
    ]


def test_search_uses_default_limit_of_five(monkeypatch):
    from app import embeddings

    captured = {}

    def fake_query(**kwargs):
        captured.update(kwargs)
        return {
            "ids": [[]],
            "documents": [[]],
            "distances": [[]],
        }

    monkeypatch.setattr(
        embeddings.collection,
        "query",
        fake_query,
    )

    search_text("test query")

    assert captured["n_results"] == 5
