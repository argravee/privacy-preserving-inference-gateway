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


def test_infer_accepts_valid_request_and_returns_job_id(api_client, monkeypatch):
    _stub_infer_execution(monkeypatch, payload_hex="deadbeef")

    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "batch_size": 1,
        "inputs": [
            {"encoding": "hex", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert isinstance(body["job_id"], str)
    assert len(body["job_id"]) > 0


def test_infer_rejects_unknown_model(api_client):
    payload = {
        "model_id": "missing_model",
        "version": "1.0.0",
        "batch_size": 1,
        "inputs": [
            {"encoding": "hex", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown model/version"


def test_infer_rejects_invalid_request_shape(api_client):
    payload = {
        "model_id": "logistic_v1",
        "inputs": [
            {"encoding": "hex", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "Invalid infer request" in response.json()["detail"]


def test_infer_rejects_non_hex_encoding(api_client):
    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "batch_size": 1,
        "inputs": [
            {"encoding": "base64", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "Invalid infer request" in response.json()["detail"]


def test_infer_rejects_invalid_hex_payload(api_client, monkeypatch):
    _stub_infer_execution(monkeypatch)

    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "batch_size": 1,
        "inputs": [
            {"encoding": "hex", "payload": "not-hex"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "not valid hex" in response.json()["detail"]


def test_infer_rejects_oversized_batch(api_client):
    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "batch_size": 17,
        "inputs": [{"encoding": "hex", "payload": "deadbeef"} for _ in range(17)],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "exceeds model max_batch_size" in response.json()["detail"]