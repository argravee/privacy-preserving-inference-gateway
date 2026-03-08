from fastapi import APIRouter, HTTPException

from server.core.jobs.queue import get_job

router = APIRouter()


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job")

    status = job["status"]

    if status == "completed":
        return {
            "status": "completed",
            "result": job["result"],
        }

    if status == "failed":
        return {
            "status": "failed",
            "error": job["error"],
        }

    return {
        "status": status,
        "job_id": job["job_id"],
    }