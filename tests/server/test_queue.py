from server.core.jobs.queue import (
    complete_job,
    create_job,
    fail_job,
    get_job,
    reset_jobs,
    start_job,
)


def test_create_job_stores_queued_job():
    reset_jobs()

    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=2,
    )

    job = get_job(job_id)
    assert job is not None
    assert job["status"] == "queued"
    assert job["model_id"] == "logistic_v1"
    assert job["version"] == "1.0.0"
    assert job["requested_batch_size"] == 2


def test_start_job_marks_running():
    reset_jobs()

    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=1,
    )
    start_job(job_id)

    job = get_job(job_id)
    assert job["status"] == "running"


def test_complete_job_stores_result_and_diagnostics():
    reset_jobs()

    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=3,
    )
    start_job(job_id)
    complete_job(
        job_id=job_id,
        payload="deadbeef",
        requested_batch_size=3,
        processed_batch_size=2,
    )

    job = get_job(job_id)

    assert job["status"] == "completed"
    assert job["result"]["model_id"] == "logistic_v1"
    assert job["result"]["version"] == "1.0.0"
    assert job["result"]["payload"] == "deadbeef"
    assert job["result"]["diagnostics"]["requested_batch_size"] == 3
    assert job["result"]["diagnostics"]["processed_batch_size"] == 2
    assert job["result"]["diagnostics"]["batch_truncated"] is True


def test_fail_job_marks_failed():
    reset_jobs()

    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=1,
    )
    fail_job(job_id, "boom")

    job = get_job(job_id)
    assert job["status"] == "failed"
    assert job["error_message"] == "boom"