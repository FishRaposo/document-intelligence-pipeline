import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChunkViewer from "@/components/ChunkViewer";
import { mockChunks } from "@/lib/mockData";

describe("ChunkViewer", () => {
  it("renders all chunks and shows the first expanded", () => {
    const chunks = mockChunks("doc-quantum-001")!;
    render(<ChunkViewer chunks={chunks} />);

    const viewer = screen.getByTestId("chunk-viewer");
    expect(viewer.querySelectorAll("li")).toHaveLength(chunks.length);

    // First chunk is expanded by default, so its full text is visible.
    expect(screen.getByText(/Quantum computing leverages qubits/)).toBeVisible();
  });

  it("toggles a collapsed chunk open on click", async () => {
    const chunks = mockChunks("doc-quantum-001")!;
    render(<ChunkViewer chunks={chunks} />);

    const buttons = screen.getAllByRole("button");
    // The second chunk starts collapsed.
    expect(buttons[1]).toHaveAttribute("aria-expanded", "false");
    await userEvent.click(buttons[1]);
    expect(buttons[1]).toHaveAttribute("aria-expanded", "true");
  });
});
