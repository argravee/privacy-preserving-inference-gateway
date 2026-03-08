from __future__ import annotations

import inspect
from typing import List

from .api import API
from .ckks.session import CKKS_Session
from .discovery import Discovery
from .errors import SchemaValidationError
from .infer import Infer
from .jobs import Jobs


class Client:
    def __init__(
            self,
            base_url: str,
            timeout: float = 5.0,
            default_headers: dict[str, str] | None = None,
            infer_schema_path: str | None = None,
    ) -> None:
        self.api = API(
            base_url=base_url,
            timeout=timeout,
            default_headers=default_headers,
        )
        self.discovery = Discovery(self.api)
        self.infer_api = Infer(self.api, schema_path=infer_schema_path)
        self.jobs = Jobs(self.api)

    def _normalize_batch(
            self,
            values: List[float] | List[List[float]],
    ) -> List[List[float]]:
        if not isinstance(values, list) or not values:
            raise SchemaValidationError("values must be a non-empty list", payload=values)

        is_number = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)

        if all(is_number(v) for v in values):
            return [[float(v) for v in values]]

        if any(not isinstance(v, list) for v in values):
            raise SchemaValidationError("values must contain only numeric values", payload=values)

        batch: List[List[float]] = []
        for row in values:
            if not row:
                raise SchemaValidationError("batch rows must be non-empty", payload=values)
            if not all(is_number(v) for v in row):
                raise SchemaValidationError("batch rows must contain only numeric values", payload=values)
            batch.append([float(v) for v in row])

        return batch

    def _validate_inputs_against_model(self, model: dict, batch: List[List[float]]) -> None:
        inference = model.get("inference", {})
        input_dimension = inference.get("input_dimension")
        if input_dimension is None:
            raise SchemaValidationError("missing inference.input_dimension", payload=model)
        if not isinstance(input_dimension, int) or input_dimension <= 0:
            raise SchemaValidationError(
                "inference.input_dimension must be a positive integer",
                payload=model,
            )

        for row in batch:
            if len(row) != input_dimension:
                raise SchemaValidationError(
                    f"expected {input_dimension} values, got {len(row)}",
                    payload=row,
                )

        constraints = model.get("constraints", {})
        max_batch_size = constraints.get("max_batch_size")
        if max_batch_size is not None:
            if not isinstance(max_batch_size, int) or max_batch_size <= 0:
                raise SchemaValidationError(
                    "max_batch_size must be a positive integer",
                    payload=model,
                )
            if len(batch) > max_batch_size:
                raise SchemaValidationError(
                    f"batch size {len(batch)} exceeds model max_batch_size {max_batch_size}",
                    payload=batch,
                )

    def infer(
            self,
            model_id: str,
            values: List[float] | List[List[float]],
            version: str | None = None,
    ) -> list[float]:
        model = self.discovery.get_model(model_id)

        if version is None:
            version = model.get("version")

        if not version:
            raise SchemaValidationError(
                f"Model '{model_id}' is missing a usable version field",
                payload=model,
            )

        batch = self._normalize_batch(values)
        self._validate_inputs_against_model(model, batch)

        session = CKKS_Session.from_model(model)

        if hasattr(session, "encrypt_feature_batch"):
            ciphertexts = session.encrypt_feature_batch(batch)
        elif hasattr(session, "encrypt_batch"):
            ciphertexts = session.encrypt_batch(batch)
        elif hasattr(session, "encrypt"):
            if len(batch) == 1:
                ct = session.encrypt(batch[0])
                ciphertexts = ct if isinstance(ct, list) else [ct]
            else:
                ciphertexts = [session.encrypt(row) for row in batch]
        else:
            raise SchemaValidationError(
                "Session object does not support encryption",
                payload=session,
            )

        submit_sig = inspect.signature(self.infer_api.submit)
        if "batch_size" in submit_sig.parameters:
            job = self.infer_api.submit(
                model_id=model_id,
                version=version,
                batch_size=len(batch),
                inputs=ciphertexts,
            )
        else:
            job = self.infer_api.submit(
                model_id=model_id,
                version=version,
                inputs=ciphertexts,
            )

        response = self.jobs.wait(job["job_id"])

        if hasattr(session, "decrypt_slots"):
            return session.decrypt_slots(response, batch_size=len(batch))

        if hasattr(session, "decrypt"):
            payload = response["payload"] if isinstance(response, dict) and "payload" in response else response
            values = session.decrypt(payload)
            if hasattr(values, "tolist"):
                values = values.tolist()
            if isinstance(values, list):
                return [float(v) for v in values[: len(batch)]]
            return [float(values)]

        raise SchemaValidationError(
            "Session object does not support decryption",
            payload=session,
        )