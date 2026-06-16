// Bundled mock dataset so every view is fully explorable with NO backend.
// Mirrors the exact response shapes of the Document Intelligence Pipeline API.
// The API client falls back to these helpers whenever a live fetch fails.

import type {
  Chunk,
  DocumentDetail,
  DocumentEntities,
  DocumentSummary,
  IngestResult,
  QuarantineEntry,
  SearchHit,
} from "@/types";

function emptyEntities(): DocumentEntities {
  return { emails: [], urls: [], phones: [], capitalised: [] };
}

// --------------------------------------------------------------------------- //
// Chunk text bodies (kept readable so the preview viewer looks real)
// --------------------------------------------------------------------------- //
const QUANTUM_CHUNKS = [
  "Quantum computing leverages qubits, which unlike classical bits can exist in a superposition of states. This property, combined with entanglement, allows quantum machines to explore an exponentially large solution space in parallel.",
  "Entanglement links the state of two or more qubits such that measuring one instantly constrains the others. Researchers at MIT and IBM have demonstrated entangled registers exceeding 1,000 physical qubits.",
  "Error correction remains the central engineering challenge. Surface codes spread a single logical qubit across many noisy physical qubits, trading hardware overhead for fault tolerance.",
  "Practical applications include Shor's algorithm for factoring, Grover's search, and quantum chemistry simulations that are intractable for classical supercomputers.",
];

const ONBOARDING_CHUNKS = [
  "Welcome to Acme Corp. This handbook covers your first 30 days, benefits enrollment, and the tools you will use day to day. Please review each section and acknowledge completion in the HR portal.",
  "Benefits enrollment closes 30 days after your start date. Health, dental, and vision plans are administered through our provider; contact benefits@acme.example for help.",
  "Our engineering org follows a trunk-based workflow. All changes go through pull requests with at least one approval and a green CI run before merge.",
  "Security is everyone's responsibility. Enable MFA on day one, never share credentials, and report phishing attempts to security@acme.example immediately.",
];

const FINANCIAL_CHUNKS = [
  "Q4 revenue grew 18% year over year to $42.3M, driven by expansion in the enterprise segment and a 22% increase in net revenue retention.",
  "Operating margin improved to 14.1% as the company realized leverage across sales and marketing. Free cash flow turned positive for the first time at $3.1M.",
  "Management guides full-year revenue of $180M to $186M, reflecting continued momentum and a healthy pipeline entering the next fiscal year.",
];

const RESEARCH_CHUNKS = [
  "We propose a retrieval-augmented generation pipeline that grounds language-model outputs in a curated corpus, reducing hallucination rates by 41% on our benchmark.",
  "The system chunks documents semantically, embeds each chunk with a 384-dimensional model, and indexes vectors for approximate nearest-neighbor search at query time.",
  "Ablation studies show that semantic chunking outperforms fixed-window chunking on answer faithfulness, particularly for long technical documents with nested structure.",
];

function toChunks(bodies: string[]): Chunk[] {
  return bodies.map((content, i) => ({
    id: `chunk-${i}-${Math.abs(hash(content))}`,
    chunk_index: i,
    content,
    word_count: content.split(/\s+/).filter(Boolean).length,
  }));
}

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  }
  return h;
}

// --------------------------------------------------------------------------- //
// Documents
// --------------------------------------------------------------------------- //
interface MockDoc {
  detail: DocumentDetail;
  chunks: Chunk[];
}

const MOCK_DOCS: MockDoc[] = [
  {
    detail: {
      id: "doc-quantum-001",
      filename: "quantum-computing-primer.md",
      format: "md",
      file_size_bytes: 18452,
      total_chunks: QUANTUM_CHUNKS.length,
      content_hash: "a1b2c3d4e5f60718293a4b5c6d7e8f90112233445566778899aabbccddeeff00",
      title: "A Primer on Quantum Computing",
      author: "Dr. Ada Reyes",
      word_count: 2840,
      entities: {
        emails: ["research@quantumlab.example"],
        urls: ["https://quantumlab.example/primer"],
        phones: [],
        capitalised: ["Quantum Computing", "MIT", "IBM", "Shor", "Grover"],
      },
      metadata: {
        title: "A Primer on Quantum Computing",
        author: "Dr. Ada Reyes",
        dates: ["2024-02-14"],
        word_count: 2840,
        char_count: 18211,
        page_count: 9,
        file_size_bytes: 18452,
        source_metadata: { generator: "Markdown" },
      },
      created_at: "2026-06-10T09:12:00Z",
    },
    chunks: toChunks(QUANTUM_CHUNKS),
  },
  {
    detail: {
      id: "doc-onboarding-002",
      filename: "employee-handbook.pdf",
      format: "pdf",
      file_size_bytes: 248901,
      total_chunks: ONBOARDING_CHUNKS.length,
      content_hash: "ff00eeddccbbaa99887766554433221100f0e1d2c3b4a5968778695a4b3c2d1e",
      title: "Acme Corp Employee Handbook",
      author: "People Operations",
      word_count: 5120,
      entities: {
        emails: ["benefits@acme.example", "security@acme.example"],
        urls: [],
        phones: ["+1 555 010 2030"],
        capitalised: ["Acme Corp", "People Operations", "HR"],
      },
      metadata: {
        title: "Acme Corp Employee Handbook",
        author: "People Operations",
        dates: ["2025-01-06"],
        word_count: 5120,
        char_count: 31480,
        page_count: 24,
        file_size_bytes: 248901,
        source_metadata: { producer: "LibreOffice", page_count: 24 },
      },
      created_at: "2026-06-11T14:03:00Z",
    },
    chunks: toChunks(ONBOARDING_CHUNKS),
  },
  {
    detail: {
      id: "doc-financial-003",
      filename: "q4-earnings-summary.html",
      format: "html",
      file_size_bytes: 9821,
      total_chunks: FINANCIAL_CHUNKS.length,
      content_hash: "0011223344556677889900aabbccddeeff112233445566778899aabbccddeeff",
      title: "Q4 Earnings Summary",
      author: "Investor Relations",
      word_count: 1430,
      entities: {
        emails: ["ir@vertex.example"],
        urls: ["https://vertex.example/investors"],
        phones: [],
        capitalised: ["Investor Relations", "Vertex"],
      },
      metadata: {
        title: "Q4 Earnings Summary",
        author: "Investor Relations",
        dates: ["2026-01-28"],
        word_count: 1430,
        char_count: 8740,
        page_count: null,
        file_size_bytes: 9821,
        source_metadata: { title: "Q4 Earnings Summary" },
      },
      created_at: "2026-06-12T08:45:00Z",
    },
    chunks: toChunks(FINANCIAL_CHUNKS),
  },
  {
    detail: {
      id: "doc-research-004",
      filename: "rag-pipeline-paper.txt",
      format: "txt",
      file_size_bytes: 41203,
      total_chunks: RESEARCH_CHUNKS.length,
      content_hash: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      title: "Retrieval-Augmented Generation at Scale",
      author: "Lin Zhao",
      word_count: 6210,
      entities: {
        emails: ["lzhao@university.example"],
        urls: ["https://arxiv.example/abs/2401.00042"],
        phones: [],
        capitalised: ["Retrieval", "Lin Zhao"],
      },
      metadata: {
        title: "Retrieval-Augmented Generation at Scale",
        author: "Lin Zhao",
        dates: ["2024-11-03"],
        word_count: 6210,
        char_count: 39022,
        page_count: 14,
        file_size_bytes: 41203,
        source_metadata: {},
      },
      created_at: "2026-06-13T16:20:00Z",
    },
    chunks: toChunks(RESEARCH_CHUNKS),
  },
];

// --------------------------------------------------------------------------- //
// Public mock API surface
// --------------------------------------------------------------------------- //
export function mockDocuments(): DocumentSummary[] {
  return MOCK_DOCS.map((d) => ({
    id: d.detail.id,
    filename: d.detail.filename,
    format: d.detail.format,
    title: d.detail.title,
    author: d.detail.author,
    total_chunks: d.detail.total_chunks,
    word_count: d.detail.word_count,
    created_at: d.detail.created_at,
  }));
}

export function mockDocument(id: string): DocumentDetail | null {
  return MOCK_DOCS.find((d) => d.detail.id === id)?.detail ?? null;
}

export function mockChunks(id: string): Chunk[] | null {
  const doc = MOCK_DOCS.find((d) => d.detail.id === id);
  return doc ? doc.chunks : null;
}

export function mockQuarantine(): QuarantineEntry[] {
  return [
    {
      id: "q-001",
      filename: "scanned-invoice.xyz",
      format: "xyz",
      file_size_bytes: 5120,
      reason: "Unsupported file format '.xyz'",
      created_at: "2026-06-12T10:30:00Z",
    },
    {
      id: "q-002",
      filename: "corrupted-report.pdf",
      format: "pdf",
      file_size_bytes: 0,
      reason: "parse error: PDF stream is empty or truncated",
      created_at: "2026-06-13T11:05:00Z",
    },
    {
      id: "q-003",
      filename: "binary-blob.bin",
      format: "bin",
      file_size_bytes: 102400,
      reason: "Unsupported file format '.bin'",
      created_at: "2026-06-14T09:14:00Z",
    },
  ];
}

/** Rank mock chunks against a query by naive token overlap. */
export function mockSearch(query: string, topK = 5): SearchHit[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
  const hits: SearchHit[] = [];

  for (const doc of MOCK_DOCS) {
    for (const chunk of doc.chunks) {
      const text = chunk.content.toLowerCase();
      const overlap = terms.reduce(
        (acc, t) => acc + (text.includes(t) ? 1 : 0),
        0
      );
      const base = terms.length ? overlap / terms.length : 0;
      // Smooth score so even non-matches rank, like a real embedding search.
      const score = Math.min(0.99, 0.35 + base * 0.6 + (overlap > 0 ? 0.05 : 0));
      hits.push({
        id: `${doc.detail.id}:${chunk.id}`,
        score: Number(score.toFixed(6)),
        document_id: doc.detail.id,
        filename: doc.detail.filename,
        chunk_id: chunk.id,
        content: chunk.content,
      });
    }
  }

  return hits.sort((a, b) => b.score - a.score).slice(0, topK);
}

/** Synthesize an IngestResult for a demo-mode upload. */
export function mockIngest(filename: string, text: string): IngestResult {
  const format = filename.includes(".")
    ? filename.split(".").pop()!.toLowerCase()
    : "txt";
  const supported = ["txt", "md", "markdown", "html", "htm", "pdf", "docx"];

  if (!supported.includes(format)) {
    return {
      status: "quarantined",
      filename,
      document_id: null,
      total_chunks: 0,
      title: null,
      metadata: {},
      entities: emptyEntities(),
      chunks: [],
      error: `Unsupported file format '.${format}'`,
      quarantine_id: `q-demo-${Math.abs(hash(filename + text))}`,
    };
  }

  const words = text.split(/\s+/).filter(Boolean);
  const chunkBodies: string[] = [];
  for (let i = 0; i < words.length; i += 60) {
    chunkBodies.push(words.slice(i, i + 60).join(" "));
  }
  if (chunkBodies.length === 0) chunkBodies.push(text || "(empty document)");

  const firstLine = (text.split("\n").find((l) => l.trim()) || filename).trim();
  const title = firstLine.replace(/^#+\s*/, "").slice(0, 120) || filename;

  return {
    status: "completed",
    filename,
    document_id: `doc-demo-${Math.abs(hash(filename + text))}`,
    total_chunks: chunkBodies.length,
    title,
    metadata: {
      title,
      author: null,
      dates: [],
      word_count: words.length,
      char_count: text.length,
      page_count: null,
      file_size_bytes: new TextEncoder().encode(text).length,
      source_metadata: {},
    },
    entities: emptyEntities(),
    chunks: chunkBodies.map((content, i) => ({
      chunk_id: i,
      content,
      word_count: content.split(/\s+/).filter(Boolean).length,
    })),
    error: null,
    quarantine_id: null,
  };
}
