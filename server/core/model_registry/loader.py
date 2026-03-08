from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .schema_validation import validate_model_registry_entry
from .semantic_validation import semantic_model_registry_validation

REGISTRY_DIR = Path(__file__).resolve().parent


class RegistryError(Exception):
    """Raised when the model registry is invalid."""


@dataclass(frozen=True)
class ModelDefinition:
    model_id: str
    version: str
    raw: dict[str, Any]


def load_model_registry() -> dict[tuple[str, str], ModelDefinition]:
    if not REGISTRY_DIR.exists():
        raise RegistryError(f"Model registry directory not found: {REGISTRY_DIR}")

    if not REGISTRY_DIR.is_dir():
        raise RegistryError(f"Model registry path is not a directory: {REGISTRY_DIR}")

    model_files = [
        p for p in REGISTRY_DIR.glob("*.json")
        if p.name != "model_registry_entry.schema.json"
    ]

    if not model_files:
        raise RegistryError("No model registry files found")

    registry: dict[tuple[str, str], ModelDefinition] = {}

    for path in model_files:
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise RegistryError(f"Invalid JSON in {path.name}: {exc}") from exc

        try:
            validate_model_registry_entry(data)
        except Exception as exc:
            raise RegistryError(
                f"Schema validation failed for {path.name}: {exc}"
            ) from exc

        try:
            semantic_model_registry_validation(data)
        except Exception as exc:
            raise RegistryError(
                f"Semantic validation failed for {path.name}: {exc}"
            ) from exc

        try:
            model_id = data["model_id"]
            version = data["version"]
        except KeyError as exc:
            raise RegistryError(
                f"Missing required field {exc.args[0]} in {path.name}"
            ) from exc

        identity = (model_id, version)
        if identity in registry:
            raise RegistryError(f"Duplicate model identity: {model_id}:{version}")

        registry[identity] = ModelDefinition(
            model_id=model_id,
            version=version,
            raw=data,
        )

    if not registry:
        raise RegistryError("Registry is empty")

    if not any(model.raw["he_scheme"] == "CKKS" for model in registry.values()):
        raise RegistryError("Model registry contains no CKKS compatible models")

    return registry