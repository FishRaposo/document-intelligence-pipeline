import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
)

from doc_pipeline.chunkers import SlidingWindowChunker
from doc_pipeline.cleaners import clean_extracted_text
from doc_pipeline.embeddings import MockEmbeddingGenerator
from doc_pipeline.parsers import DocumentParser

SAMPLE_TEXT = (
    "Artificial intelligence is transforming software engineering. "
    "Modern IDEs feature intelligent code agents. "
    "These systems require robust data ingestion to fetch knowledge "
    "and answer query context accurately. "
    "The pipeline processes documents, splits them into chunk "
    "parameters, and embeds them into vector databases."
)


def main():
    temp_file = "sample_doc.txt"
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)

    print(f"--- Processing {temp_file} through Ingestion Pipeline ---")
    parser = DocumentParser()
    raw = parser.parse_file(temp_file)
    cleaned = clean_extracted_text(raw)

    chunker = SlidingWindowChunker(chunk_size=15, overlap=5)
    chunks = chunker.chunk_text(cleaned)

    embedder = MockEmbeddingGenerator(dimension=128)
    for ch in chunks:
        ch["embedding"] = embedder.embed_text(ch["content"])

    print(f"Extracted {len(chunks)} overlapping semantic chunks:")
    for i, ch in enumerate(chunks):
        print(
            f" Chunk {i}: '{ch['content']}' "
            f"(Vector size: {len(ch['embedding'])})"
        )

    os.remove(temp_file)


if __name__ == "__main__":
    main()
