"""Business-service templates used by the future API endpoint implementations."""

from typing import Any


def load_workspace() -> dict[str, Any]:
    """Assemble the local workspace summary from project, run, and dataset records."""
    ...


def search_model_catalog(query: str, cursor: str | None) -> dict[str, Any]:
    """Find supported Hugging Face models matching a query and pagination cursor."""
    ...


def collect_hardware_profile() -> dict[str, Any]:
    """Detect hardware and runtime capabilities on the machine that executes jobs."""
    ...


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