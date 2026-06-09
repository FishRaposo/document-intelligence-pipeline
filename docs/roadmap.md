# Project Roadmap - Document Intelligence Pipeline

This document outlines the development roadmap and key phases of the Document Intelligence Pipeline.

---

## Milestone 1: Core Processing Pipeline (Completed)
- **Multi-Format Extraction Skeletons**: Standardize parser entry points for PDF, DOCX, HTML, and text.
- **Text Cleaning Engine**: Strip boilerplate, normalize whitespace, and repair character encodings.
- **Parametric Chunking**: Support fixed-size and sliding-window chunking strategies.
- **JSONL Metadata Exporter**: Format chunk outputs into structured, RAG-ready JSONL files detailing file origin, index, and tokens.

---

## Milestone 2: Background Workers & Visualization UI (Planned)
- **Asynchronous Processing Workers**: Offload file parsing tasks to background processes using Celery and Redis.
- **Interactive Chunk Previewer**: A browser dashboard where users can drag-and-drop a PDF, view the generated text chunks side-by-side, inspect extracted metadata tags, and preview token costs.
- **Direct Database Export**: Integrate pgvector storage to automatically load generated chunks and embeddings into a database index.
- **Error Quarantine Management**: Create a dedicated file storage directory to hold corrupted or unsupported files for manual inspection.

---

## Milestone 3: Advanced Intelligence & Production Scale (Future)
- **OCR Integration**: Embed Tesseract or deep-learning-based OCR to parse image-only scanned PDFs.
- **PII Redaction Layer**: Automatically detect and mask names, email addresses, phone numbers, and keys before tokenizing text.
- **Semantic Deduplication**: Implement MinHash LSH algorithms to isolate and filter duplicated chunks across large corpuses.
- **Auto-Scaling Workers**: Deploy workers in containers that scale dynamically based on the queue depth of the ingest directories.
