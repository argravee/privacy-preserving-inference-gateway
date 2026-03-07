from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from .api import API
from .errors import JobFailedError, JobTimeoutError, SchemaValidationError


class Jobs:
    """
    Manage asynchronous inference jobs.
    """

    def __init__(self, api: API, schema_path: str | Path | None = None):
        self.api = api
        self._infer_response_schema = self._load_schema(schema_path)

    def wait(
            self,
            job_id: str,
            interval: float = 1.0,
            timeout: float | None = 60.0,
    ) -> dict[str, Any]:
        """
        Poll job status until completion.

        Supports two common server patterns:
        1. Wrapped job response:
           { "status": "queued|running|completed|failed", ... }
        2. Direct final response:
           infer.response.schema.json shape
        """
        start_time = time.time()

        while True:
            response = self.api.get(f"/jobs/{job_id}")

            # Pattern 1: explicit job wrapper
            if isinstance(response, dict) and "status" in response:
                status = response.get("status")

                if status in {"queued", "running", "pending"}:
                    if timeout is not None and (time.time() - start_time) > timeout:
                        raise JobTimeoutError(f"Job {job_id} exceeded timeout")
                    time.sleep(interval)
                    continue

                if status == "failed":
                    raise JobFailedError(
                        job_id=job_id,
                        reason=response.get("error") or response.get("message") or "Unknown error",
                    )

                if status == "completed":
                    # Some APIs return the final payload directly in `result`
                    result = response.get("result", response)
                    self._validate_final_response(result)
                    return result

                raise SchemaValidationError(
                    f"Unknown job status '{status}'",
                    payload=response,
                )

            # Pattern 2: server returns final infer response directly
            self._validate_final_response(response)
            return response

    def _validate_final_response(self, payload: dict) -> None:
        try:
            validate(instance=payload, schema=self._infer_response_schema)
        except ValidationError as exc:
            raise SchemaValidationError(
                f"Final inference response failed schema validation: {exc.message}",
                payload=payload,
            ) from exc

    @staticmethod
    def _load_schema(schema_path: str | Path | None) -> dict:
        if schema_path is None:
            schema_path = (
                    Path(__file__).resolve().parents[3]
                    / "schemas"
                    / "infer.response.schema.json"
            )
        else:
            schema_path = Path(schema_path)

        with schema_path.open("r", encoding="utf-8") as f:
            return json.load(f)