import { test, expect } from "@playwright/test";

// Smoke E2E: navigate the dashboard in demo mode (no backend running).
// Each data view should fall back to bundled mock data and the demo-mode
// indicator should appear.

test("overview loads and shows the processing summary", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Document Intelligence/i);
  await expect(
    page.getByRole("heading", { name: "Overview" })
  ).toBeVisible();
  await expect(page.getByText("Processing summary")).toBeVisible();
  // No backend in CI → demo-mode badge should surface.
  await expect(page.getByTestId("demo-mode-badge")).toBeVisible();
});

test("documents list renders and opens a detail page", async ({ page }) => {
  await page.goto("/documents");
  await expect(
    page.getByRole("heading", { name: "Documents" })
  ).toBeVisible();
  await expect(page.getByTestId("document-list")).toBeVisible();

  await page.getByText("A Primer on Quantum Computing").click();
  await expect(page).toHaveURL(/\/documents\/doc-quantum-001/);
  await expect(page.getByTestId("chunk-viewer")).toBeVisible();
});

test("search returns ranked chunks", async ({ page }) => {
  await page.goto("/search");
  await page.getByLabel("Search query").fill("qubits superposition");
  await page.getByRole("button", { name: /search/i }).click();
  await expect(page.getByTestId("search-results")).toBeVisible();
});

test("quarantine view lists failed files", async ({ page }) => {
  await page.goto("/quarantine");
  await expect(
    page.getByRole("heading", { name: "Quarantine" })
  ).toBeVisible();
  await expect(page.getByTestId("quarantine-list")).toBeVisible();
});
