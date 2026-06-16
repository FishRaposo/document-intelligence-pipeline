import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import ProcessingStats from "@/components/ProcessingStats";
import { mockDocuments, mockQuarantine } from "@/lib/mockData";

describe("ProcessingStats", () => {
  it("summarizes document, chunk, and quarantine totals", () => {
    const docs = mockDocuments();
    const quarantine = mockQuarantine();
    render(<ProcessingStats documents={docs} quarantine={quarantine} />);

    expect(screen.getByText("Documents")).toBeInTheDocument();
    expect(screen.getByText("Total chunks")).toBeInTheDocument();

    // Document count matches the dataset size.
    expect(screen.getByText(String(docs.length))).toBeInTheDocument();
    // Quarantine count is surfaced.
    expect(screen.getByText("Quarantined")).toBeInTheDocument();
  });

  it("renders the format chart when documents exist", () => {
    render(
      <ProcessingStats documents={mockDocuments()} quarantine={[]} />
    );
    expect(screen.getByTestId("format-chart")).toBeInTheDocument();
  });
});
