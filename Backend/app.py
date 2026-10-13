from fastapi import Body, FastAPI, File, Form, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from api.operations import create_project as create_project_operation
from api.operations import (
    estimate_run,
    get_hardware_profile,
    get_workspace,
    import_dataset as import_dataset_operation,
    search_models,
)
from services.health import get_health

app = FastAPI(title="Local Foundry API", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["GET"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return get_health()


@app.get("/api/hardware-profile")
def hardware_profile() -> dict:
    return get_hardware_profile()


@app.get("/api/workspace")
def workspace() -> dict:
    return get_workspace()


@app.get("/api/models")
def models(query: str = "", cursor: str | None = None, limit: int = Query(default=20, ge=1, le=100)) -> dict:
    return search_models(query, cursor, limit)


@app.post("/api/estimates")
def estimate(configuration: dict = Body(...)) -> dict:
    return estimate_run(configuration)


@app.post("/api/datasets/import", status_code=201)
def import_dataset(file: UploadFile = File(...), workflow: str = Form(...)) -> dict:
    return import_dataset_operation(file, workflow)


@app.post("/api/projects", status_code=201)
def create_project(project: dict) -> dict:
    return create_project_operation(project)