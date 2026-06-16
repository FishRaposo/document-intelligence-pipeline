import "@testing-library/jest-dom";

// recharts' ResponsiveContainer relies on ResizeObserver, which jsdom lacks.
if (typeof globalThis.ResizeObserver === "undefined") {
  class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver =
    ResizeObserver as unknown as typeof globalThis.ResizeObserver;
}
