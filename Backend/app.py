from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.operations import get_hardware_profile
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