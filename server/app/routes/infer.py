from fastapi import APIRouter, Depends, HTTPException, status
from jsonschema import ValidationError as JsonSchemaValidationError

from server.core.crypto.backend import CryptoBackend
from server.core.crypto.ciphertxt_validation import validate_ciphertext_structure
from server.core.crypto.crypto_backends.ckks_pyfhel.context import generate_ckks_context
from server.core.crypto.dependencies import get_crypto_backend
from server.core.he_execution.logistic import evaluate_encrypted_logistic
from server.core.jobs.queue import complete_job, create_job, start_job
from server.core.model_registry.registry import MODEL_REGISTRY
from server.core.protocol.envelope_validation import validate_envelope
from server.core.security.rate_limits import enforce_infer_rate_limit
from server.core.security.tenanting import get_tenant_id
from server.core.crypto.crypto_backends.ckks_pyfhel.context import CKKS_CONTEXT, generate_ckks_context

router = APIRouter()

def get_crypto_context():
    return CKKS_CONTEXT

@router.post("/infer", status_code=status.HTTP_200_OK)
def infer(
        envelope: dict,
        tenant_id: str = Depends(get_tenant_id),
        backend: CryptoBackend = Depends(get_crypto_backend),
):
    enforce_infer_rate_limit(tenant_id)

    try:
        validate_envelope(envelope)
    except (JsonSchemaValidationError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid infer request: {exc}",
        ) from exc

    model_id = envelope["model_id"]
    version = envelope["version"]
    inputs = envelope["inputs"]
    batch_size = envelope["batch_size"]

    model_meta = MODEL_REGISTRY.get((model_id, version))
    if model_meta is None:
        raise HTTPException(status_code=404, detail="Unknown model/version")

    encryption_parameters = model_meta.raw.get("encryption_parameters", {})
    try:
        crypto_params = {
            "scheme": model_meta.raw.get("he_scheme", "CKKS"),
            "poly_modulus_degree": encryption_parameters["poly_modulus_degree"],
            "coeff_modulus_bits": encryption_parameters["coeff_modulus_bits"],
            "scale": encryption_parameters["scale"],
        }
    except KeyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Model registry missing CKKS parameter: {exc.args[0]}",
        ) from exc

    context = generate_ckks_context(crypto_params)

    constraints = model_meta.raw.get("constraints", {})
    max_batch_size = constraints.get("max_batch_size")
    if isinstance(max_batch_size, int) and batch_size > max_batch_size:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Batch size {batch_size} exceeds model max_batch_size "
                f"{max_batch_size}"
            ),
        )

    input_dimension = model_meta.raw.get("inference", {}).get("input_dimension")
    if len(inputs) not in {1, input_dimension}:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expected either 1 pre-aggregated ciphertext or "
                f"{input_dimension} feature ciphertexts, got {len(inputs)}"
            ),
        )

    feature_ciphertexts = []

    for item in inputs:
        if item.get("encoding") != "hex":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported input encoding: {item.get('encoding')}",
            )

        try:
            raw_ciphertext = bytes.fromhex(item["payload"])
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Input payload is not valid hex",
            ) from exc

        try:
            ct = validate_ciphertext_structure(
                raw_ciphertext=raw_ciphertext,
                model_meta=model_meta,
                context=context,
                backend=backend,
            )
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid ciphertext: {exc}",
            ) from exc

        feature_ciphertexts.append(ct)

    job_id = create_job(
        tenant_id=tenant_id,
        model_id=model_id,
        version=version,
        requested_batch_size=batch_size,
    )

    try:
        start_job(job_id)

        result_ct = evaluate_encrypted_logistic(
            feature_ciphertexts=feature_ciphertexts,
            model_raw=model_meta.raw,
            context=context,
        )

        result_payload = result_ct.to_bytes().hex()

        complete_job(
            job_id=job_id,
            payload=result_payload,
            requested_batch_size=batch_size,
            processed_batch_size=batch_size,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Inference execution failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "status": "completed",
        "job_id": job_id,
    }