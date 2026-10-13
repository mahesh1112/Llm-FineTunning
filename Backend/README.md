# Python API

This backend currently exposes `GET /api/health` and `GET /api/hardware-profile`. Health and hardware-profile logic live in `services/`; the API modules expose thin handlers. `api/health.py` keeps a provider-neutral WSGI callable; `app.py` is the ASGI adapter used by local Uvicorn development.

## Planned function templates

`api/operations.py` contains unrouted HTTP function stubs for workspace data, model search, run estimates, dataset import, project creation, and evaluation start/status. The hardware-profile function is implemented and registered as `/api/hardware-profile`.

`services/operations.py` contains the implemented hardware discovery service plus business-service stubs for assembling workspace data, searching the model catalog, resource estimation, dataset validation/storage, project persistence, and evaluation jobs/results.

The remaining operation templates contain descriptions and placeholders only. They are not connected to `app.py` and do not create live routes.

## Run locally with Uvicorn

From the workspace root, install the local HTTP adapter dependencies:

```powershell
python -m pip install -r Backend/requirements.txt
```

After installing dependencies, start the backend from the workspace root:

```powershell
uvicorn app:app --app-dir Backend --reload --host 127.0.0.1 --port 8000
```

Verify in a browser or another terminal at `http://127.0.0.1:8000/api/health` and `http://127.0.0.1:8000/api/hardware-profile`. The hardware response includes OS, CPU, memory, disk, runtime, and detected GPU information. A `null` or `Unknown` field means it could not be detected; it is not inferred as zero. GPU detection is based on a PyTorch runtime available in the environment.

The frontend uses the hardcoded local API origin `http://127.0.0.1:8000`. Start it separately from the workspace root with `npm --prefix frontend run dev`. The UI health request should show **API connected**. The workspace and other routes are not implemented and remain preview/unavailable as appropriate.

The WSGI callable can still be invoked by a future hosting adapter. No cloud provider or deployment configuration is selected here. The Vite and Uvicorn commands are local development servers and must remain running while testing locally.

Run the provider-neutral WSGI function tests from this `Backend/` directory:

```powershell
python -B -m unittest discover -s tests -v
```

## Current execution limits

This endpoint is stateless and short-lived. Existing training scripts are not connected to it. Model training is long-running and writes checkpoints/artifacts, so a serverless request should not run training inline. That feature will need a durable job/worker and persistent artifact storage, designed separately from this health endpoint.