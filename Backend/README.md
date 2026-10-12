# Python API

This backend currently exposes one endpoint: `GET /api/health`. The response logic is isolated in `services/health.py`. `api/health.py` keeps a provider-neutral WSGI callable; `app.py` is a small ASGI adapter for local Uvicorn development.

## Planned function templates

`api/operations.py` contains unrouted HTTP function stubs for workspace data, model search, hardware profile, run estimates, dataset import, project creation, and evaluation start/status. Each is intended to validate/request HTTP data and delegate to its service counterpart.

`services/operations.py` contains the matching business-service stubs for assembling workspace data, searching the model catalog, hardware discovery, resource estimation, dataset validation/storage, project persistence, and evaluation jobs/results.

These functions contain descriptions and placeholders only. They are not connected to `app.py`, do not execute work, and do not create live API routes. The health endpoint remains the only implemented route.

## Run locally with Uvicorn

From the workspace root, install the local HTTP adapter dependencies:

```powershell
python -m pip install -r Backend/requirements.txt
```

After installing dependencies, start the backend from the workspace root:

```powershell
uvicorn app:app --app-dir Backend --reload --host 127.0.0.1 --port 8000
```

Verify in a browser or another terminal at `http://127.0.0.1:8000/api/health`. Expected JSON: `{"status":"ok","service":"local-foundry-api"}`.

The frontend uses the hardcoded local API origin `http://127.0.0.1:8000`. Start it separately from the workspace root with `npm --prefix frontend run dev`. The UI health request should show **API connected**. The workspace and other routes are not implemented and remain preview/unavailable as appropriate.

The WSGI callable can still be invoked by a future hosting adapter. No cloud provider or deployment configuration is selected here. The Vite and Uvicorn commands are local development servers and must remain running while testing locally.

Run the provider-neutral WSGI function tests from this `Backend/` directory:

```powershell
python -B -m unittest discover -s tests -v
```

## Current execution limits

This endpoint is stateless and short-lived. Existing training scripts are not connected to it. Model training is long-running and writes checkpoints/artifacts, so a serverless request should not run training inline. That feature will need a durable job/worker and persistent artifact storage, designed separately from this health endpoint.