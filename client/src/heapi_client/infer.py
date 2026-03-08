import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from .api import API
from .errors import SchemaValidationError


class Infer:
    def __init__(self, api: API, schema_path: str | Path | None = None):
        self.api = api
        self.schema = None

        if schema_path is not None:
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

    def submit(
            self,
            model_id: str,
            version: str,
            inputs: list[dict[str, Any]],
            batch_size: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "model_id": model_id,
            "version": version,
            "inputs": inputs,
        }
        if batch_size is not None:
            payload["batch_size"] = batch_size

        if self.schema is not None:
            try:
                validate(payload, self.schema)
            except ValidationError as exc:
                raise SchemaValidationError(
                    f"Infer request payload failed schema validation: {exc.message}",
                    payload=payload,
                ) from exc

        return self.api.post("/infer", json=payload)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self.api.get(f"/jobs/{job_id}")