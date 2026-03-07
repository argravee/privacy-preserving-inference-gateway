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
            values: List[float],
            version: str | None = None,
    ):
        """
        Perform encrypted inference end-to-end.

        Steps:
        1. Discover model metadata
        2. Create a CKKS session from model crypto policy
        3. Encrypt inputs
        4. Submit inference
        5. Poll job status
        6. Decrypt result
        """
        model = self.discovery.get_model(model_id)

        if version is None:
            version = model.get("version")

        if not version:
            raise SchemaValidationError(
                f"Model '{model_id}' is missing a usable version field",
                payload=model,
            )

        session = CKKS_Session.from_model(model)
        ciphertext = session.encrypt(values)

        job = self.infer_api.submit(
            model_id=model_id,
            version=version,
            inputs=[ciphertext],
        )

        response = self.jobs.wait(job["job_id"])
        return session.decrypt(response)