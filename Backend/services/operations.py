"""Business services and templates used by the API endpoint implementations."""

import base64
import binascii
import json
import platform
import re
import shutil
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
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


def search_model_catalog(query: str, cursor: str | None, limit: int = 20) -> dict[str, Any]:
    """Find supported Hugging Face models matching a query and pagination cursor."""
    if not 1 <= limit <= 100:
        raise ValueError("Model search limit must be between 1 and 100.")
    if cursor:
        request_url = _decode_model_cursor(cursor)
    else:
        parameters = urllib.parse.urlencode({
            "search": query.strip(),
            "limit": limit,
            "sort": "downloads",
            "direction": "-1",
        })
        request_url = f"https://huggingface.co/api/models?{parameters}"

    request = urllib.request.Request(
        request_url,
        headers={"Accept": "application/json", "User-Agent": "LocalFoundry/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            records = json.loads(response.read().decode("utf-8"))
            next_cursor = _encode_next_link(response.headers.get("Link"))
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Hugging Face returned HTTP {error.code} for model search.") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError("Could not reach the Hugging Face model catalog.") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("Hugging Face returned an invalid model catalog response.") from error

    if not isinstance(records, list):
        raise RuntimeError("Hugging Face returned an unexpected model catalog response.")

    return {
        "items": [_format_model_record(record) for record in records if isinstance(record, dict)],
        "nextCursor": next_cursor,
        "source": "huggingface",
    }


def _format_model_record(record: dict[str, Any]) -> dict[str, Any]:
    model_id = record.get("modelId") or record.get("id")
    card_data = record.get("cardData") or {}
    config = record.get("config") or {}
    safe_tensor_data = record.get("safetensors") or {}
    parameter_counts = safe_tensor_data.get("parameters") or {}
    parameter_count = max(
        (count for count in parameter_counts.values() if isinstance(count, int)),
        default=None,
    ) if isinstance(parameter_counts, dict) else None
    tags = record.get("tags") or []
    license_name = card_data.get("license")
    if not license_name:
        license_name = next((tag.removeprefix("license:") for tag in tags if tag.startswith("license:")), None)

    return {
        "id": model_id,
        "name": model_id,
        "parameters": _format_parameter_count(parameter_count),
        "family": record.get("pipeline_tag") or "Hugging Face model",
        "description": card_data.get("description") or "",
        "license": license_name or "Unknown",
        "context": config.get("max_position_embeddings") or "Unknown",
        "download": "Unknown",
        "downloads": record.get("downloads"),
        "likes": record.get("likes"),
        "methods": "",
        "capability": "Catalog result",
        "tone": "neutral",
    }


def _format_parameter_count(value: int | None) -> str:
    if value is None:
        return "Unknown"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _encode_next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    for link in link_header.split(","):
        match = re.search(r"<([^>]+)>\s*;\s*rel=\"?next\"?", link)
        if match:
            target = match.group(1)
            _validate_model_catalog_url(target)
            return base64.urlsafe_b64encode(target.encode("utf-8")).decode("ascii").rstrip("=")
    return None


def _decode_model_cursor(cursor: str) -> str:
    try:
        padded_cursor = cursor + "=" * (-len(cursor) % 4)
        target = base64.urlsafe_b64decode(padded_cursor.encode("ascii")).decode("utf-8")
        _validate_model_catalog_url(target)
        return target
    except (ValueError, UnicodeError, binascii.Error) as error:
        raise ValueError("Invalid model catalog cursor.") from error


def _validate_model_catalog_url(target: str) -> None:
    parsed = urllib.parse.urlsplit(target)
    if parsed.scheme != "https" or parsed.netloc != "huggingface.co" or parsed.path != "/api/models":
        raise ValueError("Model catalog pagination cursor is not valid.")


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
    workflow = str(configuration.get("workflow", "")).strip()
    supported_workflows = {
        "instructional_finetuning",
        "continued_pretraining",
        "distillation",
        "quantization",
    }
    if workflow not in supported_workflows:
        raise ValueError("Unsupported workflow for resource estimation.")

    hardware = collect_hardware_profile()
    missing_inputs: list[str] = []
    assumptions: list[str] = []

    if workflow == "quantization":
        workload_size = configuration.get("estimatedModelSizeBytes")
        measured_rate = configuration.get("measuredBytesPerSecond")
        rate_name = "measuredBytesPerSecond"
        if not isinstance(workload_size, int) or workload_size <= 0:
            missing_inputs.append("estimatedModelSizeBytes")
        else:
            assumptions.append("Quantization time is based on model file size and a measured local processing rate.")
    else:
        workload_size = configuration.get("estimatedTokens")
        dataset_size = configuration.get("datasetSizeBytes")
        if workload_size is None and isinstance(dataset_size, int) and dataset_size > 0:
            workload_size = max(1, round(dataset_size / 4))
            assumptions.append("Token count is estimated as dataset bytes divided by four; tokenize the dataset for a better estimate.")
        if not isinstance(workload_size, int) or workload_size <= 0:
            missing_inputs.append("estimatedTokens or datasetSizeBytes")

        epochs = configuration.get("epochs", 1)
        if not isinstance(epochs, int) or not 1 <= epochs <= 100:
            raise ValueError("Epochs must be an integer between 1 and 100.")
        workload_size = workload_size * epochs if isinstance(workload_size, int) else None
        measured_rate = configuration.get("measuredTokensPerSecond")
        rate_name = "measuredTokensPerSecond"
        assumptions.append("The range uses observed throughput for this model, technique, sequence length, and hardware.")

    if not isinstance(measured_rate, (int, float)) or measured_rate <= 0:
        missing_inputs.append(rate_name)

    if missing_inputs:
        assumptions.append("No duration is reported until workload size and a measured local throughput are available.")
        return {
            "status": "needs_calibration",
            "minSeconds": None,
            "maxSeconds": None,
            "confidence": "unknown",
            "hardware": hardware,
            "assumptions": assumptions,
            "missingInputs": missing_inputs,
        }

    processing_seconds = workload_size / measured_rate
    return {
        "status": "estimated",
        "minSeconds": max(1, round(processing_seconds * 0.8 + 60)),
        "maxSeconds": max(1, round(processing_seconds * 1.5 + 180)),
        "confidence": "low",
        "hardware": hardware,
        "assumptions": assumptions + ["The range adds setup and finalization overhead; runtime may vary."],
        "missingInputs": [],
    }


def validate_and_store_dataset(file: Any, workflow: str) -> dict[str, Any]:
    """Validate an uploaded dataset, store it, and return its fingerprint and metadata."""
    ...


def save_project(project: dict[str, Any]) -> dict[str, Any]:
    """Persist a project configuration and return the created project record."""
    name = str(project.get("name", "")).strip()
    description = str(project.get("description", "")).strip()
    workflow = str(project.get("workflow", "")).strip()
    technique = str(project.get("technique", "")).strip()
    model_id = str(project.get("modelId", "")).strip()
    model_name = str(project.get("modelName", model_id)).strip()
    dataset = project.get("dataset")
    dataset_id = dataset.get("id") if isinstance(dataset, dict) else project.get("datasetId")

    if not name or len(name) > 60:
        raise ValueError("Project name must contain between 1 and 60 characters.")
    if workflow not in {
        "instructional_finetuning",
        "continued_pretraining",
        "distillation",
        "quantization",
    }:
        raise ValueError("Unsupported project workflow.")
    if not model_id or not model_name:
        raise ValueError("A base model is required.")
    if workflow != "quantization" and not dataset_id:
        raise ValueError("A dataset is required for this workflow.")

    project_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    with connect() as connection:
        connection.execute(
            "INSERT INTO projects "
            "(id, name, description, workflow, technique, model_id, model_name, "
            "dataset_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)",
            (
                project_id,
                name,
                description,
                workflow,
                technique,
                model_id,
                model_name,
                dataset_id,
                timestamp,
                timestamp,
            ),
        )

    return {
        "id": project_id,
        "name": name,
        "description": description,
        "workflow": workflow,
        "technique": technique,
        "modelId": model_id,
        "modelName": model_name,
        "model": model_name,
        "datasetId": dataset_id,
        "runCount": 0,
        "lastRunStatus": "Draft",
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }


def queue_evaluation(run_id: str, dataset_id: str) -> dict[str, Any]:
    """Create an evaluation job for a trained model and a held-out dataset."""
    ...


def read_evaluation(evaluation_id: str) -> dict[str, Any]:
    """Load the current evaluation job status and any available metric results."""
    ...