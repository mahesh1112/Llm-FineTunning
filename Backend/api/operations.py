"""HTTP endpoint functions and templates for workspace and model operations.

Unimplemented functions are intentionally not registered in ``app.py`` yet.
Implemented endpoints delegate to their matching service functions.
"""

from typing import Any

from fastapi import HTTPException

from services.operations import (
    collect_hardware_profile as collect_hardware_profile_service,
    load_workspace as load_workspace_service,
    save_project as save_project_service,
)


def get_workspace() -> dict[str, Any]:
    """Return project, run, dataset, model, hardware, and evaluation summaries."""
    return load_workspace_service()


def search_models(query: str = "", cursor: str | None = None) -> dict[str, Any]:
    """Search the supported Hugging Face model catalog and return a result page."""
    ...


def get_hardware_profile() -> dict[str, Any]:
    """Return the execution worker's detected hardware and runtime capabilities."""
    return collect_hardware_profile_service()


def estimate_run(configuration: dict[str, Any]) -> dict[str, Any]:
    """Estimate runtime and resource requirements for a proposed workflow."""
    ...


def import_dataset(file: Any, workflow: str) -> dict[str, Any]:
    """Accept a dataset upload and return its stored identity and metadata."""
    ...


def create_project(project: dict[str, Any]) -> dict[str, Any]:
    """Create a project record from its selected workflow, model, and dataset."""
    try:
        return save_project_service(project)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def start_evaluation(run_id: str, dataset_id: str) -> dict[str, Any]:
    """Queue evaluation of a completed run against a held-out dataset."""
    ...


def get_evaluation(evaluation_id: str) -> dict[str, Any]:
    """Return evaluation job status and metrics when the job has completed."""
    ...