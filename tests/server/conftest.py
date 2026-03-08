import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from fastapi.testclient import TestClient

from server.app.main import app
from server.core.jobs import queue as queue_module
from server.core.model_registry.loader import ModelDefinition


@pytest.fixture
def sample_model_dict():
    return {
        "model_id": "logistic_v1",
        "version": "1.0.0",
        "description": "Encrypted logistic regression for binary classification",
        "he_scheme": "CKKS",
        "encryption_parameters": {
            "poly_modulus_degree": 16384,
            "scale": 1073741824,
            "coeff_modulus_bits": [60, 30, 30, 60],
            "max_multiplicative_depth": 2,
        },
        "inference": {
            "input_dimension": 8,
            "output_dimension": 1,
            "activation": "polynomial_sigmoid_v1",
        },
        "constraints": {
            "max_batch_size": 16,
        },
    }


@pytest.fixture
def sample_model_definition(sample_model_dict):
    return ModelDefinition(
        model_id=sample_model_dict["model_id"],
        version=sample_model_dict["version"],
        raw=sample_model_dict,
    )


@pytest.fixture(autouse=True)
def clear_job_state():
    queue_module.reset_jobs()
    yield
    queue_module.reset_jobs()


@pytest.fixture
def api_client(monkeypatch, sample_model_definition):
    import server.app.routes.models as models_route
    import server.app.routes.infer as infer_route

    registry = {
        (sample_model_definition.model_id, sample_model_definition.version): sample_model_definition
    }

    monkeypatch.setattr(models_route, "MODEL_REGISTRY", registry)
    monkeypatch.setattr(infer_route, "MODEL_REGISTRY", registry)

    monkeypatch.setattr(
        infer_route,
        "validate_ciphertext_structure",
        lambda **kwargs: {"validated": True},
    )

    app.dependency_overrides[infer_route.get_crypto_backend] = lambda: object()
    app.dependency_overrides[infer_route.get_crypto_context] = lambda: object()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()