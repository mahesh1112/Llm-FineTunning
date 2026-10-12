# Local Foundry frontend

This React/Vite app calls the local Python API at `http://127.0.0.1:8000`. For now, change that constant in `src/lib/api.js` if the API moves. GitHub Pages only serves the frontend; it cannot host the Python API.

## Run locally

From the workspace root, install backend dependencies once and start Uvicorn in one terminal:

```powershell
python -m pip install -r Backend/requirements.txt
uvicorn app:app --app-dir Backend --reload --host 127.0.0.1 --port 8000
```

Then, from the workspace root in another terminal, start the frontend:

```powershell
npm --prefix frontend install
npm --prefix frontend run dev
```

Open the Vite URL (normally `http://localhost:5173`) and choose **API Test**. With the backend running, the request should return the health JSON. Stop either local server with `Ctrl+C`.

## Connect the Python API

The frontend currently hardcodes its local API origin. The adapter calls these routes when the corresponding functionality is implemented:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check that the Python service is reachable |
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

The browser sends cross-origin requests, so configure the API's CORS allowlist for the frontend origin. Keep Hugging Face credentials and all other secrets on the Python service.

## GitHub Pages

For a future GitHub Pages deployment, the hardcoded local origin will need to be changed to the selected hosted API origin in `src/lib/api.js`. Build with the repository-specific base path, for example `VITE_BASE_PATH=/<repository-name>/`, then:

```powershell
npm ci
npm run build
```

Publish the generated `dist/` directory using a GitHub Pages Actions workflow. No deployment is configured by this project.

## Serverless and hardware limits

- A serverless function sees its own runtime resources, not the visitor's GPU, RAM, or disk. The hardware endpoint must describe the actual execution worker. For local execution, a separately installed local agent/API is needed to inspect the customer's machine.
- Fine-tuning is a long-running, resource-intensive job. The Python function should validate and enqueue a job for a persistent worker, then return a job identifier; do not run GPU training inside a short-lived serverless request.
- Serverless providers commonly limit request size, duration, and temporary disk. For large datasets, use an authenticated upload handshake and direct-to-object-storage upload instead of forwarding the file through the function. The current UI uses a multipart import endpoint.
- GitHub Pages has no private runtime configuration. Do not put API keys, Hugging Face tokens, or credentials in frontend environment variables.

For the first health-function implementation and local connection commands, see [Backend/README.md](../Backend/README.md). Only `/api/health` is implemented; other API features are not yet connected to Python.

## Preview scope

The preview model catalog is a small sample and does not search Hugging Face. In preview mode uploaded files remain in the browser and are not persisted. Configure the Python API before treating model availability, estimates, project storage, or training status as real.