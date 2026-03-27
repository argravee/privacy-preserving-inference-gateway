import pytest

from server.core.plain_execution.logistic import evaluate_plain_logistic


def test_evaluate_plain_logistic_returns_single_output():
    model_raw = {
        "parameters": {
            "weights": [0.2, -0.1, 0.05, 0.4],
            "bias": 0.1,
        },
        "activation_parameters": {
            "coefficients": [0.5, 0.15, -0.01],
        },
    }

    outputs = evaluate_plain_logistic(
        feature_vector=[1.0, 2.0, -1.0, 0.5],
        model_raw=model_raw,
    )

    assert isinstance(outputs, list)
    assert len(outputs) == 1
    assert isinstance(outputs[0], float)


def test_evaluate_plain_logistic_rejects_wrong_dimension():
    model_raw = {
        "parameters": {
            "weights": [0.2, -0.1, 0.05, 0.4],
            "bias": 0.1,
        },
        "activation_parameters": {
            "coefficients": [0.5, 0.15, -0.01],
        },
    }

    with pytest.raises(ValueError, match="Expected 4 input features"):
        evaluate_plain_logistic(
            feature_vector=[1.0, 2.0],
            model_raw=model_raw,
        )


def test_evaluate_plain_logistic_applies_polynomial_by_degree():
    model_raw = {
        "parameters": {
            "weights": [1.0],
            "bias": 0.0,
        },
        "activation_parameters": {
            "coefficients": [1.0, 2.0, 3.0],
        },
    }

    outputs = evaluate_plain_logistic(
        feature_vector=[2.0],
        model_raw=model_raw,
    )

    # 1 + 2*(2^1) + 3*(2^2) = 1 + 4 + 12 = 17
    assert outputs == [17.0]