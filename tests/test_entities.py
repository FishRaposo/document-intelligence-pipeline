"""Heuristic entity-extraction tests."""

from doc_pipeline.entities import extract_entities


class TestEntities:
    def test_emails(self):
        e = extract_entities("Reach a@b.com or admin@example.org today.")
        assert "a@b.com" in e["emails"]
        assert "admin@example.org" in e["emails"]

    def test_urls_strip_trailing_punctuation(self):
        e = extract_entities(
            "Visit https://example.com. Also http://test.org/path, ok."
        )
        assert "https://example.com" in e["urls"]
        assert "http://test.org/path" in e["urls"]

    def test_capitalised_ngrams(self):
        e = extract_entities("Jane Smith met Acme Corporation in Paris.")
        assert "Jane Smith" in e["capitalised"]
        assert "Acme Corporation" in e["capitalised"]

    def test_stopword_starts_filtered(self):
        e = extract_entities("The Report covers Quantum Mechanics.")
        assert "The Report" not in e["capitalised"]
        assert "Quantum Mechanics" in e["capitalised"]

    def test_phones(self):
        e = extract_entities("Call 555-123-4567 or +1 555 987 6543 now.")
        assert any("555" in p for p in e["phones"])

    def test_empty_text(self):
        e = extract_entities("")
        assert e == {"emails": [], "urls": [], "phones": [], "capitalised": []}

    def test_dedup(self):
        e = extract_entities("a@b.com a@b.com a@b.com")
        assert e["emails"] == ["a@b.com"]
