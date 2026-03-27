from __future__ import annotations

import json
from pathlib import Path

from jsonschema import validate


SCHEMA_PATH = (
        Path(__file__).resolve().parents[3]
        / "schemas"
        / "infer_plain.request.schema.json"
)

with SCHEMA_PATH.open("r", encoding="utf-8") as f:
    INFER_PLAIN_REQUEST_SCHEMA = json.load(f)


def validate_plain_envelope(envelope: dict) -> None:
    validate(instance=envelope, schema=INFER_PLAIN_REQUEST_SCHEMA)