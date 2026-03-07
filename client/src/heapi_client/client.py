from __future__ import annotations

from typing import List

from .api import API
from .discovery import Discovery
from .infer import Infer
from .jobs import Jobs
from .ckks.session import CKKS_Session
from .errors import SchemaValidationError


class Client:
    """
    High-level SDK interface for encrypted inference.
    """

    def __init__(self, base_url: str):
        self.api = API(base_url)
        self.discovery = Discovery(self.api)
        self.infer_api = Infer(self.api)
        self.jobs = Jobs(self.api)

    def infer(
            self,
            model_id: str,
            values: List[float] | List[List[float]],
            version: str | None = None,
    ):
        """
        Perform encrypted inference end-to-end.

        Accepts either:
        - a single input vector: List[float]
        - a batch of input vectors: List[List[float]]

        Steps:
        1. Discover model metadata
        2. Normalize values into a batch
        3. Validate input dimension and batch size
        4. Create a CKKS session from model metadata
        5. Encrypt each input vector
        6. Submit inference
        7. Poll job status
        8. Decrypt result
        """
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
        ciphertexts = [session.encrypt(vector) for vector in batch]

        job = self.infer_api.submit(
            model_id=model_id,
            version=version,
            inputs=ciphertexts,
        )

        response = self.jobs.wait(job["job_id"])
        return session.decrypt(response)

    def _normalize_batch(
            self,
            values: List[float] | List[List[float]],
    ) -> List[List[float]]:
        """
        Normalize either a single vector or a batch into List[List[float]].
        """
        if not isinstance(values, list) or len(values) == 0:
            raise SchemaValidationError(
                "values must be a non-empty list of floats or list of float vectors",
                payload={"values": values},
            )

        first = values[0]

        # Single vector: [0.1, 0.2, 0.3]
        if isinstance(first, (int, float)):
            if not all(isinstance(x, (int, float)) for x in values):
                raise SchemaValidationError(
                    "Single input vector must contain only numeric values",
                    payload={"values": values},
                )
            return [list(values)]

        # Batch: [[...], [...]]
        if isinstance(first, list):
            for vector in values:
                if not isinstance(vector, list):
                    raise SchemaValidationError(
                        "Batched inputs must be a list of vectors",
                        payload={"values": values},
                    )
                if len(vector) == 0:
                    raise SchemaValidationError(
                        "Input vectors must not be empty",
                        payload={"values": values},
                    )
                if not all(isinstance(x, (int, float)) for x in vector):
                    raise SchemaValidationError(
                        "Each input vector must contain only numeric values",
                        payload={"values": values},
                    )
            return values

        raise SchemaValidationError(
            "values must be a numeric vector or a batch of numeric vectors",
            payload={"values": values},
        )

    def _validate_inputs_against_model(
            self,
            model: dict,
            batch: List[List[float]],
    ) -> None:
        """
        Validate client inputs against discovered model constraints.
        """
        inference = model.get("inference", {})
        constraints = model.get("constraints", {})

        input_dimension = inference.get("input_dimension")
        max_batch_size = constraints.get("max_batch_size")

        if input_dimension is None:
            raise SchemaValidationError(
                "Model metadata missing inference.input_dimension",
                payload=model,
            )

        if not isinstance(input_dimension, int) or input_dimension < 1:
            raise SchemaValidationError(
                "Model inference.input_dimension must be a positive integer",
                payload=model,
            )

        if max_batch_size is not None:
            if not isinstance(max_batch_size, int) or max_batch_size < 1:
                raise SchemaValidationError(
                    "Model constraints.max_batch_size must be a positive integer",
                    payload=model,
                )

            if len(batch) > max_batch_size:
                raise SchemaValidationError(
                    f"Batch size {len(batch)} exceeds model max_batch_size {max_batch_size}",
                    payload={"batch_size": len(batch), "max_batch_size": max_batch_size},
                )

        for i, vector in enumerate(batch):
            if len(vector) != input_dimension:
                raise SchemaValidationError(
                    f"Input vector at batch index {i} has dimension {len(vector)}, "
                    f"expected {input_dimension}",
                    payload={
                        "batch_index": i,
                        "actual_dimension": len(vector),
                        "expected_dimension": input_dimension,
                    },
                )