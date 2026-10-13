# Python API

This backend currently exposes `GET /api/health`, `GET /api/hardware-profile`, and `GET /api/workspace`. Their service logic lives in `services/`; the API modules expose thin handlers. `api/health.py` keeps a provider-neutral WSGI callable; `app.py` is the ASGI adapter used by local Uvicorn development.

## Planned function templates

`api/operations.py` contains implemented delegates for workspace and hardware profile, plus unrouted HTTP function stubs for model search, run estimates, dataset import, project creation, and evaluation start/status.

`services/operations.py` contains implemented hardware discovery and workspace summary services plus business-service stubs for searching the model catalog, resource estimation, dataset validation/storage, project persistence, and evaluation jobs/results.

Workspace data is read from the local SQLite database; the remaining operation templates contain descriptions and placeholders and do not create live routes.

## Run locally with Uvicorn

From the workspace root, install the local HTTP adapter dependencies:

```powershell
python -m pip install -r Backend/requirements.txt
```

After installing dependencies, start the backend from the workspace root:

```powershell
uvicorn app:app --app-dir Backend --reload --host 127.0.0.1 --port 8000
```

Verify in a browser or another terminal at `http://127.0.0.1:8000/api/health`, `http://127.0.0.1:8000/api/hardware-profile`, and `http://127.0.0.1:8000/api/workspace`. The hardware response includes OS, CPU, memory, disk, runtime, and detected GPU information. A `null` or `Unknown` field means it could not be detected; it is not inferred as zero. GPU detection is based on a PyTorch runtime available in the environment.

The frontend uses the hardcoded local API origin `http://127.0.0.1:8000`. Start it separately from the workspace root with `npm --prefix frontend run dev`. The UI health request should show **API connected**. Projects, runs, and datasets are empty until created; model search and other operation routes are not implemented yet.

The WSGI callable can still be invoked by a future hosting adapter. No cloud provider or deployment configuration is selected here. The Vite and Uvicorn commands are local development servers and must remain running while testing locally.

Run the provider-neutral WSGI function tests from this `Backend/` directory:

```powershell
python -B -m unittest discover -s tests -v
```

## Current execution limits

This endpoint is stateless and short-lived. Existing training scripts are not connected to it. Model training is long-running and writes checkpoints/artifacts, so a serverless request should not run training inline. That feature will need a durable job/worker and persistent artifact storage, designed separately from this health endpoint.