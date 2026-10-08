# Python API

This backend currently exposes one endpoint: `GET /api/health`. The API is a provider-neutral WSGI callable, and the response logic is isolated in `services/health.py`. It does not start a web server or keep a process running.

## Verify the function without a server

From the `Backend/` directory:

```powershell
python -m unittest discover -s tests -v
```

The tests call the WSGI function in-process. They cover the health response, browser CORS preflight, unsupported methods, and unimplemented routes.

## HTTP and serverless integration

The WSGI callable is `api.health.application`. A future hosting adapter should map HTTP requests to this callable and invoke it per request. Choose and add a provider adapter only after selecting a deployment platform. No cloud SDK, web framework, server, or provider configuration is required by the API/service code today.

For local manual HTTP testing only, an optional WSGI development server may be used. It is not required for function tests and is not the intended production runtime.

The React frontend already requests `GET /api/health` from the configured `VITE_API_BASE_URL`; no frontend URL or framework change is needed. Other routes listed in the frontend contract are not implemented yet and return 404.

## Current execution limits

This endpoint is stateless and short-lived. Existing training scripts are not connected to it. Model training is long-running and writes checkpoints/artifacts, so a serverless request should not run training inline. That feature will need a durable job/worker and persistent artifact storage, designed separately from this health endpoint.