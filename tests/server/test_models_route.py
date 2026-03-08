def test_models_route_returns_api_version_and_models(api_client):
    response = api_client.get("/models")

    assert response.status_code == 200

    body = response.json()
    assert body["api_version"] == "1.0.0"
    assert isinstance(body["models"], list)
    assert len(body["models"]) == 1

    model = body["models"][0]
    assert model["model_id"] == "logistic_v1"
    assert model["version"] == "1.0.0"
    assert model["he_scheme"] == "CKKS"
    assert model["encryption_parameters"]["poly_modulus_degree"] == 16384
    assert model["inference"]["input_dimension"] == 8
    assert model["constraints"]["max_batch_size"] == 16