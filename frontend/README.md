# Local Foundry frontend

This React/Vite app is a static frontend. It can run with sample preview data or call a separately hosted Python API. GitHub Pages only serves the built frontend; it does not run Python functions or training jobs.

## Run locally

```powershell
npm install
npm run dev
```

Without `VITE_API_BASE_URL`, the app uses sample data. In preview mode, selecting a dataset does not upload its contents and estimates are illustrative.

## Connect the Python API

Set `VITE_API_BASE_URL` to the API origin, without a trailing slash or `/api` suffix. The frontend calls these routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/workspace` | Dashboard projects, runs, datasets, model summaries, and evaluation summary |
| `GET` | `/api/models?query=&limit=20&cursor=` | Search the Hugging Face-backed model catalog; return `{ "items": [{ "id": "org/model", "name": "org/model", "parameters": "7B" }], "nextCursor": null }` |
| `GET` | `/api/hardware-profile` | Hardware profile for the machine that will execute the job |
| `POST` | `/api/estimates` | Estimate a workflow from model, technique, dataset size, and hardware profile |
| `POST` | `/api/datasets/import` | Multipart form fields `file` and `workflow`; return `{ "id": "...", "name": "...", "sizeBytes": 123 }` |
| `POST` | `/api/projects` | Create the configured project and job request |
| `POST` | `/api/evaluations` | Start evaluation with `{ "runId": "...", "datasetId": "..." }`; return an evaluation job ID and status |
| `GET` | `/api/evaluations/{id}` | Poll job status and return metrics when evaluation completes |

Estimate requests contain `workflow`, `modelId`, `technique`, `datasetSizeBytes`, and `hardwareProfile`. Return `minSeconds`, `maxSeconds`, `confidence`, and optional `assumptions`. Model results may include `nextCursor` for pagination.

Mark held-out datasets in `/api/workspace` with `role: "evaluation"` or `split: "validation" | "test"`. Evaluation results should include `status`, `modelName`, `datasetName`, `samplesEvaluated`, and a `metrics` array. Each metric may provide `name`, numeric `value`, display-ready `formatted`, and `direction` (`higher` or `lower`). Failed jobs should include a readable `message`.

The browser sends cross-origin requests, so configure the API's CORS allowlist for the exact GitHub Pages origin. Keep Hugging Face credentials and all other secrets on the Python service; `VITE_*` values are embedded in public JavaScript and are not secret.

## GitHub Pages

Copy `.env.example` values into the GitHub Actions build environment (repository **Variables** are appropriate for these public values). Set `VITE_BASE_PATH` to `/<repository-name>/` for a project site, or `/` for a user/org site or custom domain. Set `VITE_API_BASE_URL` to the HTTPS Python API origin. Build with:

```powershell
npm ci
npm run build
```

Publish the generated `dist/` directory using a GitHub Pages Actions workflow. The repository name and API host are deployment-specific, so they are intentionally not hard-coded here.

## Serverless and hardware limits

- A serverless function sees its own runtime resources, not the visitor's GPU, RAM, or disk. The hardware endpoint must describe the actual execution worker. For local execution, a separately installed local agent/API is needed to inspect the customer's machine.
- Fine-tuning is a long-running, resource-intensive job. The Python function should validate and enqueue a job for a persistent worker, then return a job identifier; do not run GPU training inside a short-lived serverless request.
- Serverless providers commonly limit request size, duration, and temporary disk. For large datasets, use an authenticated upload handshake and direct-to-object-storage upload instead of forwarding the file through the function. The current UI uses a multipart import endpoint.
- GitHub Pages has no private runtime configuration. Do not put API keys, Hugging Face tokens, or credentials in frontend environment variables.

## Preview scope

The preview model catalog is a small sample and does not search Hugging Face. In preview mode uploaded files remain in the browser and are not persisted. Configure the Python API before treating model availability, estimates, project storage, or training status as real.