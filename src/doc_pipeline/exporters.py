"""JSONL / RAG-ready export of document chunks.

Each line is one JSON record. ``to_records`` shapes a document + its chunks into
the RAG-ready record format consumed downstream by ``rag-evaluation-lab`` and
``personal-knowledge-base-os``: a stable ``id``, the chunk ``text``, and a
``metadata`` block carrying provenance (document id, filename, title, chunk index).
"""

import json
from typing import Any, Dict, List, Optional


class JSONLExporter:
    """Writes chunk records as JSON Lines."""

    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path

    def export(self, chunks: List[Dict[str, Any]], output_path: Optional[str] = None):
        """Write ``chunks`` (one JSON object per line) to disk."""
        path = output_path or self.output_path
        if path is None:
            raise ValueError("No output_path provided for export")
        with open(path, "w", encoding="utf-8") as handle:
            for chunk in chunks:
                handle.write(json.dumps(chunk) + "\n")

    def dumps(self, chunks: List[Dict[str, Any]]) -> str:
        """Return the JSONL representation as a string (for HTTP responses)."""
        return "\n".join(json.dumps(chunk) for chunk in chunks)


def to_rag_records(
    document: Dict[str, Any], chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Shape a document + chunks into RAG-ready export records."""
    doc_id = document.get("id")
    filename = document.get("filename")
    title = document.get("title")
    records: List[Dict[str, Any]] = []
    for chunk in chunks:
        idx = chunk.get("chunk_index", chunk.get("chunk_id", 0))
        records.append(
            {
                "id": f"{doc_id}:{idx}",
                "text": chunk.get("content", ""),
                "metadata": {
                    "document_id": doc_id,
                    "filename": filename,
                    "title": title,
                    "chunk_index": idx,
                    "word_count": chunk.get("word_count", 0),
                },
            }
        )
    return records
