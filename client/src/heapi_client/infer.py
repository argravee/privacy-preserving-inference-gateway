from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import validate, ValidationError

from .api import API
from .errors import SchemaValidationError


class Infer:
    """
    Submit encrypted inference requests.
    """

    def __init__(self, api: API, schema_path: str | Path | None = None):
        self.api = api
        self._schema = self._load_schema(schema_path)

    def submit(
            self,
            model_id: str,
            version: str,
            inputs: list[dict],
    ) -> dict[str, Any]:
        """
        Submit inference request.

        inputs must be:
        [
            { "encoding": "...", "payload": "..." }
        ]
        """

        payload = {
            "model_id": model_id,
            "version": version,
            "inputs": inputs,
        }

        self._validate_request(payload)

        return self.api.post("/infer", payload)

    # Schema Validation
    def _validate_request(self, payload: dict) -> None:
        try:
            validate(instance=payload, schema=self._schema)
        except ValidationError as exc:
            raise SchemaValidationError(
                f"Inference request failed schema validation: {exc.message}",
                payload=payload,
            ) from exc

    # Load Schema
    @staticmethod
    def _load_schema(schema_path: str | Path | None) -> dict:
        if schema_path is None:
            schema_path = (
                    Path(__file__).resolve().parents[3]
                    / "schemas"
                    / "infer.request.schema.json"
            )
        else:
            schema_path = Path(schema_path)

        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)