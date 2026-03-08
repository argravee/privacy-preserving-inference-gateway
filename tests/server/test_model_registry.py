import json

import pytest

from server.core.model_registry.loader import RegistryError, load_model_registry


def _write_model(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_model_registry_valid(monkeypatch, tmp_path, sample_model_dict):
    import server.core.model_registry.loader as loader_module

    monkeypatch.setattr(loader_module, "REGISTRY_DIR", tmp_path)

    _write_model(tmp_path / "logistic_v1.json", sample_model_dict)

    registry = load_model_registry()

    assert ("logistic_v1", "1.0.0") in registry
    model = registry[("logistic_v1", "1.0.0")]
    assert model.model_id == "logistic_v1"
    assert model.version == "1.0.0"
    assert model.raw["he_scheme"] == "CKKS"


def test_load_model_registry_raises_on_duplicate_identity(monkeypatch, tmp_path, sample_model_dict):
    import server.core.model_registry.loader as loader_module

    monkeypatch.setattr(loader_module, "REGISTRY_DIR", tmp_path)

    _write_model(tmp_path / "a.json", sample_model_dict)
    _write_model(tmp_path / "b.json", sample_model_dict)

    with pytest.raises(RegistryError, match="Duplicate model identity"):
        load_model_registry()


def test_load_model_registry_raises_when_empty(monkeypatch, tmp_path):
    import server.core.model_registry.loader as loader_module

    monkeypatch.setattr(loader_module, "REGISTRY_DIR", tmp_path)

    with pytest.raises(RegistryError, match="No model registry files found"):
        load_model_registry()