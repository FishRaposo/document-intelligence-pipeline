import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ListSkeleton, CardSkeleton } from "@/components/LoadingSkeleton";
import EmptyState from "@/components/EmptyState";
import ErrorMessage from "@/components/ErrorMessage";
import ErrorBoundary from "@/components/ErrorBoundary";

describe("loading / empty / error states", () => {
  it("renders an animated list skeleton", () => {
    render(<ListSkeleton rows={3} />);
    const skeleton = screen.getByTestId("list-skeleton");
    expect(skeleton.querySelectorAll(".animate-pulse")).toHaveLength(3);
  });

  it("renders a card skeleton", () => {
    const { container } = render(<CardSkeleton />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("renders an empty state with title and description", () => {
    render(<EmptyState title="Nothing here" description="Add something" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Add something")).toBeInTheDocument();
  });

  it("renders an error message and fires onRetry", async () => {
    const onRetry = vi.fn();
    render(<ErrorMessage message="Boom" onRetry={onRetry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Boom");
    await userEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});

function Boom(): JSX.Element {
  throw new Error("kaboom");
}

describe("ErrorBoundary", () => {
  it("catches a render error and shows a fallback", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("kaboom")).toBeInTheDocument();
    spy.mockRestore();
  });
});
