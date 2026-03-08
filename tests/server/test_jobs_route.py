from server.core.jobs.queue import complete_job, create_job, fail_job
import server.app.routes.infer as infer_route


class FakeResultCiphertext:
    def __init__(self, payload_hex: str):
        self._payload = bytes.fromhex(payload_hex)

    def to_bytes(self) -> bytes:
        return self._payload


def _stub_infer_execution(monkeypatch, payload_hex: str = "deadbeef"):
    monkeypatch.setattr(infer_route, "enforce_infer_rate_limit", lambda tenant_id: None)
    monkeypatch.setattr(infer_route, "generate_ckks_context", lambda params: object())
    monkeypatch.setattr(
        infer_route,
        "validate_ciphertext_structure",
        lambda raw_ciphertext, model_meta, context, backend: object(),
    )
    monkeypatch.setattr(
        infer_route,
        "evaluate_encrypted_logistic",
        lambda feature_ciphertexts, model_raw, context: FakeResultCiphertext(payload_hex),
    )


def test_jobs_route_returns_completed_result_after_infer(api_client, monkeypatch):
    _stub_infer_execution(monkeypatch, payload_hex="deadbeef")

    infer_response = api_client.post(
        "/infer",
        json={
            "model_id": "logistic_v1",
            "version": "1.0.0",
            "batch_size": 1,
            "inputs": [{"encoding": "hex", "payload": "deadbeef"}],
        },
    )

    assert infer_response.status_code == 200
    job_id = infer_response.json()["job_id"]

    response = api_client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "completed"
    assert body["result"]["model_id"] == "logistic_v1"
    assert body["result"]["version"] == "1.0.0"
    assert body["result"]["payload"] == "deadbeef"
    assert body["result"]["diagnostics"]["requested_batch_size"] == 1
    assert body["result"]["diagnostics"]["processed_batch_size"] == 1
    assert body["result"]["diagnostics"]["batch_truncated"] is False


def test_jobs_route_returns_404_for_unknown_job(api_client):
    response = api_client.get("/jobs/missing-job")

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown job"


def test_jobs_route_returns_failed_job_wrapper(api_client):
    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=1,
    )
    fail_job(job_id, "worker crashed")

    response = api_client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error"] == "worker crashed"


def test_jobs_route_returns_direct_completed_wrapper(api_client):
    job_id = create_job(
        model_id="logistic_v1",
        version="1.0.0",
        requested_batch_size=1,
    )
    complete_job(
        job_id=job_id,
        payload="deadbeef",
        requested_batch_size=1,
        processed_batch_size=1,
    )

    response = api_client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"]["payload"] == "deadbeef"