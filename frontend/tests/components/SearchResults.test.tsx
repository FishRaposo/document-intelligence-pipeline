import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import SearchResults from "@/components/SearchResults";
import { mockSearch } from "@/lib/mockData";

describe("SearchResults", () => {
  it("renders ranked hits with similarity scores", () => {
    const hits = mockSearch("qubits superposition entanglement", 5);
    render(<SearchResults hits={hits} />);

    const list = screen.getByTestId("search-results");
    expect(list.querySelectorAll("li")).toHaveLength(hits.length);

    // Scores are shown as percentages.
    expect(screen.getAllByTitle("Similarity score").length).toBe(hits.length);
    expect(screen.getAllByText(/%$/).length).toBeGreaterThan(0);
  });

  it("ranks the most relevant chunk first", () => {
    const hits = mockSearch("qubits superposition", 5);
    // Top result should mention qubits/superposition.
    render(<SearchResults hits={hits} />);
    const list = screen.getByTestId("search-results");
    const firstItem = list.querySelector("li");
    expect(firstItem?.textContent?.toLowerCase()).toMatch(
      /qubit|superposition|entangle/
    );
  });
});
