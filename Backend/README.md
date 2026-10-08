# Local Foundry Python function

This folder contains the first serverless endpoint: `GET /api/health`. It uses Python's standard library and has no package dependencies.

## Test locally

From the workspace root, start the function:

```powershell
python Backend/api/health.py
```

In another terminal, verify the JSON response:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected response: `status: ok`, `service: local-foundry-api`.

To connect the Vite frontend locally, run these commands from `frontend/` in a separate terminal:

```powershell
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev -- --host 127.0.0.1 --port 5174
```

The top bar should change to **API connected**. The workspace stays on preview data until its API routes are implemented.

## Deploy to Vercel

Create a Vercel project for this repository and set its **Root Directory** to `Backend`. Vercel maps `api/health.py` to `/api/health`. Deploy the project, then set the frontend build variable `VITE_API_BASE_URL` to the deployed origin (for example, `https://your-project.vercel.app`) and rebuild the GitHub Pages site.

This endpoint only returns non-sensitive health information and allows cross-origin GET/OPTIONS requests. Before adding private data or state-changing routes, replace the wildcard origin with the exact frontend origin and add appropriate authentication.