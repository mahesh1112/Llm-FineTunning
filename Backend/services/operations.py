"""Business services and templates used by the API endpoint implementations."""

import json
import platform
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
from services.storage import connect


def load_workspace() -> dict[str, Any]:
    """Assemble the local workspace summary from project, run, and dataset records."""
    with connect() as connection:
        project_rows = connection.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        run_rows = connection.execute(
            "SELECT runs.*, projects.name AS project_name "
            "FROM runs LEFT JOIN projects ON projects.id = runs.project_id "
            "ORDER BY runs.updated_at DESC"
        ).fetchall()
        dataset_rows = connection.execute(
            "SELECT * FROM datasets ORDER BY created_at DESC"
        ).fetchall()
        evaluation_row = connection.execute(
            "SELECT metrics_json FROM evaluations "
            "WHERE status = 'completed' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()

    runs_by_project: dict[str, list[sqlite3.Row]] = {}
    for run in run_rows:
        runs_by_project.setdefault(run["project_id"], []).append(run)

    projects = []
    for project in project_rows:
        project_runs = runs_by_project.get(project["id"], [])
        latest_status = project_runs[0]["status"] if project_runs else project["status"]
        projects.append({
            "id": project["id"],
            "name": project["name"],
            "description": project["description"],
            "model": project["model_name"],
            "runCount": len(project_runs),
            "lastRunStatus": latest_status.title(),
            "updatedLabel": project["updated_at"],
        })

    runs = []
    for run in run_rows:
        status = run["status"]
        runs.append({
            "id": run["id"],
            "name": run["name"],
            "project": run["project_name"] or "Unknown project",
            "projectId": run["project_id"],
            "model": run["model_name"],
            "method": run["method"],
            "status": status.title(),
            "tone": _status_tone(status),
            "updated": run["updated_at"],
            "datasetId": run["dataset_id"],
        })

    datasets = []
    for dataset in dataset_rows:
        size_mb = dataset["size_bytes"] / (1024 * 1024)
        datasets.append({
            "id": dataset["id"],
            "projectId": dataset["project_id"],
            "name": dataset["name"],
            "detail": f"{size_mb:.1f} MB · Fingerprint {dataset['fingerprint'][:12]}",
            "format": dataset["format"],
            "rows": dataset["row_count"] if dataset["row_count"] is not None else "—",
            "status": dataset["status"].title(),
            "role": dataset["role"],
        })

    evaluation_metrics = json.loads(evaluation_row["metrics_json"] or "[]") if evaluation_row else []
    return {
        "projects": projects,
        "runs": runs,
        "datasets": datasets,
        "machine": collect_hardware_profile(),
        "models": [],
        "lastEvaluation": evaluation_metrics[0]["formatted"] if evaluation_metrics else "—",
    }


def _status_tone(status: str) -> str:
    return {
        "passed": "success",
        "completed": "success",
        "warning": "warning",
        "failed": "danger",
        "error": "danger",
        "queued": "neutral",
        "training": "running",
        "evaluating": "running",
    }.get(status.lower(), "neutral")


def search_model_catalog(query: str, cursor: str | None) -> dict[str, Any]:
    """Find supported Hugging Face models matching a query and pagination cursor."""
    ...


def collect_hardware_profile() -> dict[str, Any]:
    """Detect host resources visible to this process without guessing unknowns."""
    try:
        memory_info = psutil.virtual_memory()
        memory = {
            "status": "available",
            "totalBytes": memory_info.total,
            "availableBytes": memory_info.available,
        }
    except (OSError, RuntimeError):
        memory = {"status": "unknown", "totalBytes": None, "availableBytes": None}

    try:
        disk_info = shutil.disk_usage(Path(__file__).resolve().parents[1])
        disk = {
            "status": "available",
            "totalBytes": disk_info.total,
            "freeBytes": disk_info.free,
        }
        storage = f"{disk_info.free / (1024 ** 3):.1f} GiB free"
    except OSError:
        disk = {"status": "unknown", "totalBytes": None, "freeBytes": None}
        storage = "Unknown"

    runtime_parts = [f"Python {platform.python_version()}"]
    gpu_status = "unknown"
    gpu_backend = None
    gpu_devices: list[dict[str, Any]] = []
    gpu_name = "Unknown"
    vram = "Unknown"
    gpu_reason = "PyTorch is not installed; GPU detection is unavailable."

    try:
        import torch
    except (ImportError, OSError):
        torch = None

    if torch is not None:
        runtime_parts.append(f"PyTorch {torch.__version__}")
        accelerator_runtime = torch.version.hip or torch.version.cuda
        if accelerator_runtime:
            runtime_parts.append(f"Accelerator runtime {accelerator_runtime}")

        try:
            if torch.cuda.is_available():
                gpu_backend = "rocm" if torch.version.hip else "cuda"
                for index in range(torch.cuda.device_count()):
                    properties = torch.cuda.get_device_properties(index)
                    gpu_devices.append({
                        "index": index,
                        "name": properties.name,
                        "memoryTotalBytes": properties.total_memory,
                    })

                if gpu_devices:
                    gpu_status = "available"
                    gpu_name = ", ".join(device["name"] for device in gpu_devices)
                    memory_total = sum(device["memoryTotalBytes"] for device in gpu_devices)
                    vram = f"{memory_total / (1024 ** 3):.1f} GiB total"
                    gpu_reason = None
                else:
                    gpu_status = "unknown"
                    gpu_reason = "PyTorch reports accelerator support but no devices were listed."
            elif torch.backends.mps.is_available():
                gpu_status = "available"
                gpu_backend = "metal"
                gpu_name = "Apple Metal"
                gpu_devices = [{"index": 0, "name": gpu_name, "memoryTotalBytes": None}]
                gpu_reason = "PyTorch does not expose total Metal device memory."
            else:
                gpu_status = "unavailable"
                gpu_reason = "PyTorch reports no CUDA, ROCm, or Metal device available to this process."
        except (AttributeError, OSError, RuntimeError) as error:
            gpu_status = "unknown"
            gpu_reason = str(error)

    return {
        "collectedAt": datetime.now(timezone.utc).isoformat(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "cpu": {
            "model": platform.processor() or None,
            "logicalCores": psutil.cpu_count(logical=True),
            "physicalCores": psutil.cpu_count(logical=False),
        },
        "memory": memory,
        "gpu": gpu_name,
        "gpuStatus": gpu_status,
        "gpuBackend": gpu_backend,
        "gpuDevices": gpu_devices,
        "gpuReason": gpu_reason,
        "vram": vram,
        "disk": disk,
        "storage": storage,
        "runtime": " · ".join(runtime_parts),
    }


def estimate_resources(configuration: dict[str, Any]) -> dict[str, Any]:
    """Calculate an estimated duration and resource range for a normalized run."""
    ...


def validate_and_store_dataset(file: Any, workflow: str) -> dict[str, Any]:
    """Validate an uploaded dataset, store it, and return its fingerprint and metadata."""
    ...


def save_project(project: dict[str, Any]) -> dict[str, Any]:
    """Persist a project configuration and return the created project record."""
    ...


def queue_evaluation(run_id: str, dataset_id: str) -> dict[str, Any]:
    """Create an evaluation job for a trained model and a held-out dataset."""
    ...


def read_evaluation(evaluation_id: str) -> dict[str, Any]:
    """Load the current evaluation job status and any available metric results."""
    ...