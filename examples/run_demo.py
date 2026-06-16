"""End-to-end demo of the Document Intelligence Pipeline (offline, no API keys).

Ingests a small corpus of in-memory documents through the full pipeline —
parse -> clean -> metadata + entities -> chunk -> dedup -> embed -> persist ->
index — then demonstrates deduplication, the error quarantine, similarity search,
and RAG-ready JSONL export. Runs with NO database and NO network: the in-memory
document store, the offline ``HashFallbackProvider`` embeddings, and the in-memory
vector store make the whole flow deterministic and dependency-light.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from shared_core.vectorstore import get_vector_store  # noqa: E402

from doc_pipeline.exporters import JSONLExporter, to_rag_records  # noqa: E402
from doc_pipeline.pipeline import DocumentPipeline  # noqa: E402
from doc_pipeline.storage import InMemoryDocumentStore  # noqa: E402

CORPUS = [
    (
        "ai-report.md",
        b"""# AI in Software Engineering
By: Dr. Ada Lovelace

Published 2024-03-01. Contact research@example.com or https://example.org.

Artificial intelligence is transforming software engineering. Modern IDEs feature
intelligent code agents. These systems require robust data ingestion to fetch
knowledge and answer query context accurately. The pipeline processes documents,
splits them into chunks, and embeds them into vector databases for retrieval.
""",
    ),
    (
        "rag-notes.html",
        b"""<html><head><title>RAG Notes</title></head><body>
<h1>Retrieval Augmented Generation</h1>
<p>Retrieval augmented generation grounds a language model in external documents.</p>
<p>A vector store returns the most similar chunks for a user query.</p>
<script>console.log('ignored')</script>
</body></html>""",
    ),
    # A duplicate of the first document (different filename) to show dedup.
    (
        "ai-report-copy.md",
        b"""# AI in Software Engineering
By: Dr. Ada Lovelace

Published 2024-03-01. Contact research@example.com or https://example.org.

Artificial intelligence is transforming software engineering. Modern IDEs feature
intelligent code agents. These systems require robust data ingestion to fetch
knowledge and answer query context accurately. The pipeline processes documents,
splits them into chunks, and embeds them into vector databases for retrieval.
""",
    ),
    # An unsupported format to show the error quarantine.
    ("broken.bin", b"\x00\x01\x02 not a parseable document"),
]


def main() -> int:
    store = InMemoryDocumentStore()
    vector_store = get_vector_store(offline=True)
    pipeline = DocumentPipeline(store, vector_store)

    print("--- Ingesting corpus through the pipeline (offline) ---")
    for filename, content in CORPUS:
        result = pipeline.ingest(content, filename)
        if result.status == "completed":
            print(
                f"  [OK]   {filename}: {result.total_chunks} chunks "
                f"| title={result.title!r} | author={result.metadata.get('author')!r}"
            )
        elif result.status == "duplicate":
            print(
                f"  [DUP]  {filename}: matched existing document {result.document_id}"
            )
        else:
            print(f"  [QUAR] {filename}: quarantined ({result.error})")

    docs = store.list_documents()
    print(f"\nStored documents: {len(docs)} (duplicates were de-duplicated)")

    print("\n--- Extracted entities (first document) ---")
    first = store.get_document(docs[0]["id"])
    ents = first.get("entities", {})
    print(f"  emails: {ents.get('emails')}")
    print(f"  urls:   {ents.get('urls')}")

    print("\n--- Error quarantine ---")
    for entry in store.list_quarantine():
        print(f"  {entry['filename']}: {entry['reason']}")

    print("\n--- Similarity search: 'how does retrieval grounding work?' ---")
    for hit in pipeline.search("how does retrieval grounding work?", top_k=3):
        snippet = (hit["content"] or "")[:70].replace("\n", " ")
        print(f"  score={hit['score']:.4f} [{hit['filename']}] {snippet}...")

    print("\n--- RAG-ready JSONL export (first document) ---")
    chunks = store.get_chunks(docs[0]["id"])
    records = to_rag_records(first, chunks)
    jsonl = JSONLExporter().dumps(records)
    print(jsonl.splitlines()[0][:120] + " ...")

    print("\nDemo complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
