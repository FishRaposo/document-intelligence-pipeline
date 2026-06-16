import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiClient, demoState } from "@/lib/api";

describe("apiClient demo-mode fallback", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    demoState.set(false);
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("falls back to mock documents and flips demo mode when fetch fails", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));

    const docs = await apiClient.listDocuments();

    expect(docs.length).toBeGreaterThan(0);
    expect(docs[0]).toHaveProperty("filename");
    expect(demoState.active).toBe(true);
  });

  it("returns mock search hits offline, ranked by score", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("offline"));

    const hits = await apiClient.search("qubits superposition", 3);

    expect(hits.length).toBeGreaterThan(0);
    expect(hits.length).toBeLessThanOrEqual(3);
    // Sorted descending by score.
    for (let i = 1; i < hits.length; i++) {
      expect(hits[i - 1].score).toBeGreaterThanOrEqual(hits[i].score);
    }
  });

  it("clears demo mode when a live call succeeds", async () => {
    demoState.set(true);
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ quarantine: [] }),
    } as Response);

    const entries = await apiClient.listQuarantine();

    expect(entries).toEqual([]);
    expect(demoState.active).toBe(false);
  });
});
