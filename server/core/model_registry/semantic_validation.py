from typing import Any


def semantic_model_registry_validation(entry: dict[str, Any]) -> None:
    he_scheme = entry["he_scheme"]

    encryption_parameters = entry["encryption_parameters"]
    poly_modulus_degree = encryption_parameters["poly_modulus_degree"]
    scale = encryption_parameters["scale"]
    coeff_modulus_bits = encryption_parameters["coeff_modulus_bits"]
    max_multiplicative_depth = encryption_parameters["max_multiplicative_depth"]

    inference = entry["inference"]
    input_dimension = inference["input_dimension"]
    output_dimension = inference["output_dimension"]
    activation = inference["activation"]

    parameters = entry.get("parameters")
    activation_parameters = entry.get("activation_parameters")

    constraints = entry["constraints"]
    max_batch_size = constraints["max_batch_size"]

    if he_scheme != "CKKS":
        raise ValueError(f"Invalid he_scheme. expected CKKS got {he_scheme}")

    if poly_modulus_degree <= 0 or (poly_modulus_degree & (poly_modulus_degree - 1)) != 0:
        raise ValueError(
            f"poly_modulus_degree must be a positive power of two, got {poly_modulus_degree}"
        )

    if scale <= 0:
        raise ValueError(f"scale must be positive, got {scale}")

    if max_multiplicative_depth < 0:
        raise ValueError(
            f"max_multiplicative_depth must be non-negative, got {max_multiplicative_depth}"
        )

    if max_multiplicative_depth > len(coeff_modulus_bits) - 1:
        raise ValueError(
            "max_multiplicative_depth exceeds available coeff_modulus_bits levels"
        )

    if input_dimension <= 0:
        raise ValueError(f"input_dimension must be positive, got {input_dimension}")

    if output_dimension <= 0:
        raise ValueError(f"output_dimension must be positive, got {output_dimension}")

    if output_dimension != 1:
        raise ValueError(
            f"logistic regression requires output_dimension == 1, got {output_dimension}"
        )

    if max_batch_size <= 0:
        raise ValueError(f"max_batch_size must be positive, got {max_batch_size}")

    if max_batch_size > poly_modulus_degree:
        raise ValueError(
            "max_batch_size cannot exceed poly_modulus_degree (packing limit)"
        )

    if activation != "polynomial_sigmoid_v1":
        raise ValueError(f"Unsupported activation: {activation}")

    if parameters is not None:
        weights = parameters["weights"]
        bias = parameters["bias"]

        if len(weights) != input_dimension:
            raise ValueError(
                f"weights length must equal input_dimension ({input_dimension}), got {len(weights)}"
            )

        if not all(isinstance(w, (int, float)) for w in weights):
            raise ValueError("all weights must be numeric")

        if not isinstance(bias, (int, float)):
            raise ValueError("bias must be numeric")

    if activation_parameters is not None:
        activation_kind = activation_parameters["kind"]
        coefficients = activation_parameters["coefficients"]

        if activation_kind != activation:
            raise ValueError(
                f"activation_parameters.kind must match inference.activation, got {activation_kind}"
            )

        if len(coefficients) != 3:
            raise ValueError("polynomial_sigmoid_v1 requires exactly 3 coefficients")

        if not all(isinstance(c, (int, float)) for c in coefficients):
            raise ValueError("activation coefficients must be numeric")

        quadratic_coeff = coefficients[2]
        required_depth = 2 if abs(quadratic_coeff) > 0 else 1
        if max_multiplicative_depth < required_depth:
            raise ValueError(
                f"activation coefficients require max_multiplicative_depth >= {required_depth}"
            )

    return None