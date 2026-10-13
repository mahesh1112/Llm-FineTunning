"""Business services and templates used by the API endpoint implementations."""

import platform
import shutil
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

import psutil


def load_workspace() -> dict[str, Any]:
    """Assemble the local workspace summary from project, run, and dataset records."""
    ...


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