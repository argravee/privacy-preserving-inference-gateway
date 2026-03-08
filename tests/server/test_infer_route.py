def test_infer_accepts_valid_request_and_returns_job_id(api_client):
    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "inputs": [
            {"encoding": "hex", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert isinstance(body["job_id"], str)
    assert len(body["job_id"]) > 0


def test_infer_rejects_unknown_model(api_client):
    payload = {
        "model_id": "missing_model",
        "version": "1.0.0",
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
        "inputs": [
            {"encoding": "base64", "payload": "deadbeef"}
        ],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "Unsupported input encoding" in response.json()["detail"]


def test_infer_rejects_invalid_hex_payload(api_client):
    payload = {
        "model_id": "logistic_v1",
        "version": "1.0.0",
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
        "inputs": [{"encoding": "hex", "payload": "deadbeef"} for _ in range(17)],
    }

    response = api_client.post("/infer", json=payload)

    assert response.status_code == 400
    assert "exceeds model max_batch_size" in response.json()["detail"]