from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from .api import API
from .errors import SchemaValidationError


class Discovery:
    """
    Client-side model discovery.

    Responsibilities:
    - Fetch model metadata from the server
    - Validate the response against the public schema
    - Return model data without assuming any crypto implementation

    Non-responsibilities:
    - Creating CKKS sessions
    - Encrypting data
    - Submitting inference jobs
    """

    def __init__(self, api: API, schema_path: str | Path | None = None):
        self.api = api
        self._schema = self._load_schema(schema_path)

    def list_models(self) -> dict[str, Any]:
        """
        Fetch and validate the model list response.
        """
        payload = self.api.get("/models")
        self._validate_models_response(payload)
        return payload

    def get_model(self, model_id: str) -> dict[str, Any]:
        """
        Return a single model object by id from the validated model list.
        """
        payload = self.list_models()
        models = payload.get("models", [])

        for model in models:
            if model.get("model_id") == model_id:
                return model

        raise ValueError(f"Model '{model_id}' not found")

    def _validate_models_response(self, payload: dict[str, Any]) -> None:
        try:
            validate(instance=payload, schema=self._schema)
        except ValidationError as exc:
            raise SchemaValidationError(
                f"Model discovery response failed schema validation: {exc.message}",
                payload=payload,
            ) from exc

    @staticmethod
    def _load_schema(schema_path: str | Path | None) -> dict[str, Any]:
        """
        Load get_models.response.schema.json.

        Default lookup assumes this structure:
        project_root/
          schemas/
            get_models.response.schema.json
          client/
            src/
              heapi_client/
                discovery.py
        """
        if schema_path is None:
            schema_path = (
                    Path(__file__).resolve().parents[3]
                    / "schemas"
                    / "get_models.response.schema.json"
            )
        else:
            schema_path = Path(schema_path)

        try:
            with schema_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Could not find model discovery schema at: {schema_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model discovery schema is not valid JSON: {schema_path}"
            ) from exc