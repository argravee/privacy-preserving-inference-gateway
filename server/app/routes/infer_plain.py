from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jsonschema import ValidationError as JsonSchemaValidationError

from server.core.jobs.queue import complete_job, create_job, start_job
from server.core.model_registry.registry import MODEL_REGISTRY
from server.core.plain_execution.logistic import evaluate_plain_logistic
from server.core.protocol.plain_envelope_validation import validate_plain_envelope
from server.core.security.rate_limits import enforce_infer_rate_limit
from server.core.security.tenanting import get_tenant_id

router = APIRouter()


@router.post("/infer/plain", status_code=status.HTTP_200_OK)
def infer_plain(
        envelope: dict,
        tenant_id: str = Depends(get_tenant_id),
):
    enforce_infer_rate_limit(tenant_id)

    try:
        validate_plain_envelope(envelope)
    except (JsonSchemaValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plain infer request: {exc}",
        ) from exc

    model_id = envelope["model_id"]
    version = envelope["version"]
    inputs = envelope["inputs"]

    model_meta = MODEL_REGISTRY.get((model_id, version))
    if model_meta is None:
        raise HTTPException(status_code=404, detail="Unknown model/version")

    input_dimension = model_meta.raw.get("inference", {}).get("input_dimension")
    if not isinstance(input_dimension, int):
        raise HTTPException(
            status_code=500,
            detail="Model registry missing inference.input_dimension",
        )

    if len(inputs) != input_dimension:
        raise HTTPException(
            status_code=400,
            detail=f"Expected {input_dimension} input features, got {len(inputs)}",
        )

    job_id = create_job(
        tenant_id=tenant_id,
        model_id=model_id,
        version=version,
        requested_batch_size=1,
    )

    try:
        start_job(job_id)

        outputs = evaluate_plain_logistic(
            feature_vector=inputs,
            model_raw=model_meta.raw,
        )

        complete_job(
            job_id=job_id,
            payload=None,
            requested_batch_size=1,
            processed_batch_size=1,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Plain inference execution failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "model_id": model_id,
        "version": version,
        "outputs": outputs,
        "diagnostics": {
            "mode": "plain",
        },
    }