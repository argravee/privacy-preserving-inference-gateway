from fastapi.testclient import TestClient

from server.app.main import app
from server.core.model_registry.registry import MODEL_REGISTRY

client = TestClient(app)


def test_infer_plain_returns_output():
    model_meta = MODEL_REGISTRY[("logistic_v1", "1.0.0")]
    input_dimension = model_meta.raw["inference"]["input_dimension"]

    response = client.post(
        "/infer/plain",
        json={
            "model_id": "logistic_v1",
            "version": "1.0.0",
            "inputs": [0.1] * input_dimension,
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()
    assert body["model_id"] == "logistic_v1"
    assert body["version"] == "1.0.0"
    assert body["diagnostics"]["mode"] == "plain"
    assert isinstance(body["outputs"], list)
    assert len(body["outputs"]) == 1
    assert isinstance(body["outputs"][0], float)


def test_infer_plain_rejects_wrong_dimension():
    model_meta = MODEL_REGISTRY[("logistic_v1", "1.0.0")]
    input_dimension = model_meta.raw["inference"]["input_dimension"]

    wrong_dimension = max(1, input_dimension - 1)
    if wrong_dimension == input_dimension:
        wrong_dimension += 1

    response = client.post(
        "/infer/plain",
        json={
            "model_id": "logistic_v1",
            "version": "1.0.0",
            "inputs": [0.1] * wrong_dimension,
        },
    )

    assert response.status_code == 400
    assert "Expected" in response.json()["detail"]


def test_infer_plain_rejects_unknown_model():
    response = client.post(
        "/infer/plain",
        json={
            "model_id": "does_not_exist",
            "version": "1.0.0",
            "inputs": [0.1, -0.2, 0.3, 0.4],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown model/version"