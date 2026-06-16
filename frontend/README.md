# Document Intelligence — Dashboard

A polished Next.js 14 dashboard for the **Document Intelligence Pipeline** FastAPI
backend. Ingest documents, browse parsed metadata and chunks, run similarity
search over the vector index, and triage failed files in the quarantine.

Built with Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS,
lucide-react, and recharts.

## Pages

| Route             | Purpose                                                   | Backend endpoint(s)                          |
| ----------------- | --------------------------------------------------------- | -------------------------------------------- |
| `/`               | Overview with a processing-stats summary chart            | `GET /documents`, `GET /quarantine`          |
| `/ingest`         | Upload a file or paste text to run the pipeline           | `POST /ingest`, `POST /ingest/text`          |
| `/documents`      | List of ingested documents with status                    | `GET /documents`                             |
| `/documents/[id]` | Document detail: metadata, entities, and a chunk viewer   | `GET /documents/{id}`, `GET /documents/{id}/chunks`, `GET /export/{id}` |
| `/search`         | Similarity search returning ranked chunks                 | `POST /search`                               |
| `/quarantine`     | Failed-file review with one-click reprocess               | `GET /quarantine`, `POST /quarantine/{id}/reprocess` |

## Getting started

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

The backend defaults to `http://localhost:8000`. To run the FastAPI service:

```bash
# from the repository root
uvicorn src.doc_pipeline.main:app --reload
```

## Demo mode (no backend required)

Every view is fully explorable with **no backend running**. The API client in
`src/lib/api.ts` always tries the live FastAPI endpoint first; if the request
fails (backend down, network error, non-OK status) it transparently falls back
to the bundled mock dataset in `src/lib/mockData.ts`. When any call falls back,
a visible **Demo mode** badge appears in the top bar.

This makes the UI showcase-ready and testable offline — just `npm run dev` and
click around, or run the component/E2E tests without standing up the API.

## Environment variables

| Variable              | Default                 | Description                          |
| --------------------- | ----------------------- | ------------------------------------ |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend.     |

Copy `.env.example` to `.env.local` to override.

## Scripts

```bash
npm run dev          # start the dev server
npm run build        # production build
npm start            # serve the production build
npm test             # run Vitest component tests (no backend needed)
npm run test:e2e     # run Playwright smoke tests (demo mode)
npx tsc --noEmit     # type-check
```

## Testing

- **Component tests** — Vitest + @testing-library/react + jsdom. They render the
  key components and pages against the bundled mock data and assert content, so
  they pass with no backend. See `tests/`.
- **E2E smoke test** — Playwright (`e2e/smoke.spec.ts`) navigates the demo-mode
  UI: overview, documents list → detail, search, and quarantine.

## Docker

The repository's root `docker-compose.yml` includes a `web` service:

```bash
# from the repository root
docker compose up web
```

It builds the `dev` stage of `frontend/Dockerfile` and serves on
`http://localhost:3000`.
