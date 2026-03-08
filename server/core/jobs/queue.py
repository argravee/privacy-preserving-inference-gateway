from __future__ import annotations

from typing import Any
from uuid import uuid4

JOB_STORE: dict[str, dict[str, Any]] = {}


def create_job(
        model_id: str,
        version: str,
        requested_batch_size: int,
        tenant_id: str = "default-tenant",
) -> str:
    job_id = uuid4().hex
    JOB_STORE[job_id] = {
        "job_id": job_id,
        "tenant_id": tenant_id,
        "model_id": model_id,
        "version": version,
        "status": "queued",
        "requested_batch_size": requested_batch_size,
    }
    return job_id


def start_job(job_id: str) -> None:
    job = JOB_STORE.get(job_id)
    if job is None:
        raise KeyError(f"Unknown job: {job_id}")
    job["status"] = "running"


def complete_job(
        job_id: str,
        payload: str,
        requested_batch_size: int,
        processed_batch_size: int,
) -> None:
    job = JOB_STORE.get(job_id)
    if job is None:
        raise KeyError(f"Unknown job: {job_id}")

    job["status"] = "completed"
    job["result"] = {
        "model_id": job["model_id"],
        "version": job["version"],
        "payload": payload,
        "diagnostics": {
            "requested_batch_size": requested_batch_size,
            "processed_batch_size": processed_batch_size,
            "batch_truncated": processed_batch_size < requested_batch_size,
        },
    }


def fail_job(job_id: str, error: str) -> None:
    job = JOB_STORE.get(job_id)
    if job is None:
        raise KeyError(f"Unknown job: {job_id}")

    job["status"] = "failed"
    job["error"] = error
    job["error_message"] = error


def get_job(job_id: str) -> dict[str, Any] | None:
    return JOB_STORE.get(job_id)


def reset_jobs() -> None:
    JOB_STORE.clear()