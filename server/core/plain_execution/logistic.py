from __future__ import annotations

from typing import Sequence


def _apply_polynomial_sigmoid(linear_value: float, coefficients: Sequence[float]) -> float:
    if not coefficients:
        raise ValueError("Polynomial sigmoid coefficients are required")

    result = 0.0

    for degree, coeff in enumerate(coefficients):
        if coeff == 0:
            continue
        result += float(coeff) * (linear_value ** degree)

    return result


def evaluate_plain_logistic(feature_vector: Sequence[float], model_raw: dict) -> list[float]:
    parameters = model_raw["parameters"]
    weights = parameters["weights"]
    bias = parameters["bias"]

    if len(feature_vector) != len(weights):
        raise ValueError(
            f"Expected {len(weights)} input features, got {len(feature_vector)}"
        )

    linear_value = 0.0

    for feature, weight in zip(feature_vector, weights):
        linear_value += float(feature) * float(weight)

    linear_value += float(bias)

    activation_parameters = model_raw["activation_parameters"]
    coefficients = activation_parameters["coefficients"]

    output = _apply_polynomial_sigmoid(linear_value, coefficients)
    return [output]