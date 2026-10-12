"""HTTP endpoint templates for workspace and model operations.

These functions are intentionally not registered in ``app.py`` yet. Each
endpoint will validate its HTTP input and delegate to the matching service
when that operation is implemented.
"""

from typing import Any


def get_workspace() -> dict[str, Any]:
    """Return project, run, dataset, model, hardware, and evaluation summaries."""
    ...


def search_models(query: str = "", cursor: str | None = None) -> dict[str, Any]:
    """Search the supported Hugging Face model catalog and return a result page."""
    ...


def get_hardware_profile() -> dict[str, Any]:
    """Return the execution worker's detected hardware and runtime capabilities."""
    ...


def estimate_run(configuration: dict[str, Any]) -> dict[str, Any]:
    """Estimate runtime and resource requirements for a proposed workflow."""
    ...


def import_dataset(file: Any, workflow: str) -> dict[str, Any]:
    """Accept a dataset upload and return its stored identity and metadata."""
    ...


def create_project(project: dict[str, Any]) -> dict[str, Any]:
    """Create a project record from its selected workflow, model, and dataset."""
    ...


def start_evaluation(run_id: str, dataset_id: str) -> dict[str, Any]:
    """Queue evaluation of a completed run against a held-out dataset."""
    ...


def get_evaluation(evaluation_id: str) -> dict[str, Any]:
    """Return evaluation job status and metrics when the job has completed."""
    ...