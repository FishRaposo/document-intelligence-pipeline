import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import IngestResultCard from "@/components/IngestResultCard";
import { mockIngest } from "@/lib/mockData";

describe("IngestResultCard", () => {
  it("shows a completed ingest with chunk count and a document link", () => {
    const result = mockIngest("notes.md", "# Hello\n\nsome body content here");
    render(<IngestResultCard result={result} />);

    expect(screen.getByTestId("ingest-result")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("notes.md")).toBeInTheDocument();
    expect(screen.getByText(/View document/)).toBeInTheDocument();
  });

  it("shows the failure reason for a quarantined ingest", () => {
    const result = mockIngest("blob.xyz", "junk");
    render(<IngestResultCard result={result} />);

    expect(screen.getByText("quarantined")).toBeInTheDocument();
    expect(
      screen.getByText(/Unsupported file format '.xyz'/)
    ).toBeInTheDocument();
  });
});
