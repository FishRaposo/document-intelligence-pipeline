import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import QuarantineList from "@/components/QuarantineList";
import { mockQuarantine } from "@/lib/mockData";

describe("QuarantineList", () => {
  it("renders each quarantined entry with its failure reason", () => {
    const entries = mockQuarantine();
    render(<QuarantineList entries={entries} />);

    const list = screen.getByTestId("quarantine-list");
    expect(list.querySelectorAll("li")).toHaveLength(entries.length);
    expect(
      screen.getByText("Unsupported file format '.xyz'")
    ).toBeInTheDocument();
    expect(screen.getByText("scanned-invoice.xyz")).toBeInTheDocument();
  });

  it("invokes onReprocess with the entry id when clicked", async () => {
    const entries = mockQuarantine();
    const onReprocess = vi.fn();
    render(<QuarantineList entries={entries} onReprocess={onReprocess} />);

    const buttons = screen.getAllByRole("button", { name: /reprocess/i });
    await userEvent.click(buttons[0]);
    expect(onReprocess).toHaveBeenCalledWith(entries[0].id);
  });
});
