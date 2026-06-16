import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import DocumentList from "@/components/DocumentList";
import { mockDocuments } from "@/lib/mockData";

describe("DocumentList", () => {
  it("renders one row per document with chunk counts", () => {
    const docs = mockDocuments();
    render(<DocumentList documents={docs} />);

    const list = screen.getByTestId("document-list");
    expect(list.querySelectorAll("li")).toHaveLength(docs.length);

    // Titles from the mock dataset render.
    expect(
      screen.getByText("A Primer on Quantum Computing")
    ).toBeInTheDocument();
    // Chunk counts render for every document.
    expect(screen.getAllByText(/chunks$/).length).toBe(docs.length);
  });

  it("links each document to its detail route", () => {
    const docs = mockDocuments();
    render(<DocumentList documents={docs} />);
    const link = screen.getByText("A Primer on Quantum Computing").closest("a");
    expect(link).toHaveAttribute("href", "/documents/doc-quantum-001");
  });
});
