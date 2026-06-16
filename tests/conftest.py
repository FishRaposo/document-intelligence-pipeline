import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from shared_core.vectorstore import get_vector_store  # noqa: E402

from doc_pipeline.pipeline import DocumentPipeline  # noqa: E402
from doc_pipeline.storage import InMemoryDocumentStore  # noqa: E402

# --------------------------------------------------------------------------- #
# Fixture documents (offline; pdf/docx live behind optional-dep skips in tests)
# --------------------------------------------------------------------------- #
SAMPLE_MD = """# Quantum Computing Report
By: Dr. Jane Smith

Published 2024-01-15. Contact research@example.com or https://example.com.

Quantum computing uses qubits to represent information in superposition.
Modern systems require robust ingestion. The pipeline chunks and embeds text.
Vectors enable similarity search across a knowledge base for retrieval.
"""

SAMPLE_HTML = (
    b"<html><head><title>HTML Doc</title></head><body>"
    b"<h1>Heading</h1><p>Paragraph one has content.</p>"
    b"<p>Paragraph two follows along nicely.</p>"
    b"<script>console.log('noise')</script></body></html>"
)

SAMPLE_TXT = (
    b"Plain text document about machine learning and data engineering. "
    b"It contains several sentences. Each sentence adds context. "
    b"The ingestion pipeline reads this content and splits it into chunks."
)


@pytest.fixture
def sample_txt_bytes():
    return (
        b"This is a sample text document.\nIt has multiple lines.\n\nAnd a blank line."
    )


@pytest.fixture
def sample_md_bytes():
    return SAMPLE_MD.encode("utf-8")


@pytest.fixture
def sample_html_bytes():
    return SAMPLE_HTML


@pytest.fixture
def sample_chunks():
    return [
        {"chunk_id": 0, "content": "first chunk", "word_count": 2},
        {"chunk_id": 1, "content": "second chunk", "word_count": 2},
    ]


@pytest.fixture
def store():
    return InMemoryDocumentStore()


@pytest.fixture
def vector_store():
    return get_vector_store(offline=True)


@pytest.fixture
def pipeline(store, vector_store):
    return DocumentPipeline(store, vector_store)
