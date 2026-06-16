"""End-to-end integration tests for the ingestion pipeline (offline)."""


class TestPipelineIngestion:
    def test_full_flow_markdown(self, pipeline, store, sample_md_bytes):
        result = pipeline.ingest(sample_md_bytes, "report.md")
        assert result.status == "completed"
        assert result.document_id is not None
        assert result.total_chunks >= 1
        assert result.title == "Quantum Computing Report"
        assert result.metadata["author"] == "Dr. Jane Smith"
        assert "research@example.com" in result.entities["emails"]
        # persisted
        assert store.get_document(result.document_id) is not None
        assert len(store.get_chunks(result.document_id)) == result.total_chunks

    def test_html_ingestion(self, pipeline, sample_html_bytes):
        result = pipeline.ingest(sample_html_bytes, "page.html")
        assert result.status == "completed"
        assert result.total_chunks >= 1

    def test_chunks_have_embeddings_indexed(
        self, pipeline, vector_store, sample_md_bytes
    ):
        pipeline.ingest(sample_md_bytes, "report.md")
        assert vector_store.count() >= 1


class TestDeduplication:
    def test_identical_document_is_duplicate(self, pipeline, sample_md_bytes):
        first = pipeline.ingest(sample_md_bytes, "report.md")
        second = pipeline.ingest(sample_md_bytes, "report-copy.md")
        assert second.status == "duplicate"
        assert second.document_id == first.document_id

    def test_only_one_document_stored(self, pipeline, store, sample_md_bytes):
        pipeline.ingest(sample_md_bytes, "a.md")
        pipeline.ingest(sample_md_bytes, "b.md")
        assert len(store.list_documents()) == 1


class TestQuarantine:
    def test_unsupported_format_quarantined(self, pipeline, store):
        result = pipeline.ingest(b"binary junk", "data.xyz")
        assert result.status == "quarantined"
        assert result.quarantine_id is not None
        entries = store.list_quarantine()
        assert len(entries) == 1
        assert entries[0]["filename"] == "data.xyz"
        assert "Unsupported format" in entries[0]["reason"]

    def test_reprocess_quarantine_failure_stays(self, pipeline, store):
        result = pipeline.ingest(b"junk", "data.xyz")
        again = pipeline.reprocess_quarantine(result.quarantine_id)
        assert again.status == "quarantined"
        # still listed because it still cannot be parsed
        assert len(store.list_quarantine()) >= 1

    def test_reprocess_broken_file_is_idempotent(self, pipeline, store):
        # A permanently-broken file must not grow the quarantine on each retry:
        # reprocessing it leaves exactly the original entry in place.
        result = pipeline.ingest(b"junk", "data.xyz")
        original_id = result.quarantine_id
        assert len(store.list_quarantine()) == 1

        for _ in range(3):
            again = pipeline.reprocess_quarantine(original_id)
            assert again.status == "quarantined"
            # The newly-created duplicate is dropped; the original survives.
            assert again.quarantine_id == original_id
            assert len(store.list_quarantine()) == 1
            assert store.get_quarantine(original_id) is not None

    def test_reprocess_missing_entry_returns_none(self, pipeline):
        assert pipeline.reprocess_quarantine("does-not-exist") is None

    def test_reprocess_recovers_after_fix(self, pipeline, store):
        # Quarantine a .xyz, then re-submit its bytes under a supported name.
        bad = pipeline.ingest(b"now parseable as text", "data.xyz")
        entry = store.get_quarantine(bad.quarantine_id)
        # Manually rename to a supported extension and reprocess.
        store._quarantine[bad.quarantine_id]["filename"] = "data.txt"  # type: ignore[attr-defined]
        recovered = pipeline.reprocess_quarantine(bad.quarantine_id)
        assert recovered.status in {"completed", "duplicate"}
        assert entry is not None


class TestSearch:
    def test_search_returns_relevant_chunk(self, pipeline, sample_md_bytes):
        pipeline.ingest(sample_md_bytes, "report.md")
        hits = pipeline.search("qubits superposition information", top_k=3)
        assert len(hits) >= 1
        assert "content" in hits[0]
        assert hits[0]["score"] is not None

    def test_search_empty_store(self, pipeline):
        assert pipeline.search("anything") == []
