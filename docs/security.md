# Security Boundaries & Rules - Document Intelligence Pipeline

This document defines the security parameters, input validation boundaries, and risk models for the Document Intelligence Pipeline.

---

## 1. Safe Ingestion & File Validation

- **Strict Extension Allowlisting**: The pipeline accepts only predefined file extensions (e.g., `.pdf`, `.docx`, `.html`, `.md`, `.txt`). All other extensions must be rejected on upload.
- **MIME-Type Verification**: File extensions are easily forged. Upload endpoints must inspect magic numbers/headers to verify that file content matches the declared MIME type.
- **File Size Caps**: Ingest boundaries must enforce a maximum size limit per file (e.g., 25MB) to mitigate denial-of-service (DoS) attempts aimed at consuming disk space or CPU cycles.

---

## 2. Sandbox Processing & Path Traversals

- **Sanitized Upload Paths**: Upload paths must be strictly checked. User-provided filenames must be stripped of directory traversal sequences (e.g., `../../`, `..\..\`) to prevent writing files to system directories.
- **Resource Constraints**: Downstream parser workers should run inside containerized environments with CPU and memory limits. This prevents malicious PDFs (like deep recursive PDF objects) from hanging the entire application host.
- **No Execute Permissions**: The upload target directory must be mounted with non-executable permissions (`noexec`) to prevent execution of malicious binary code disguised as document files.

---

## 3. Data Protection and Confidentiality

- **Access Controls on Output**: Exporter folders containing chunked JSONL datasets must be protected by directory-level permissions. Output payloads often contain sensitive company IP.
- **PII Awareness**: Ingested documents may contain PII. Telemetry dashboards must never log the raw text of chunks or private metadata fields.
- **Vector Database Ingestion Boundary**: If chunks are exported to pgvector, access to the database credentials must be strictly controlled, and transit traffic should be encrypted.
