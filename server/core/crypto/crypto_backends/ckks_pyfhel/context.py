from __future__ import annotations

from typing import Any

from Pyfhel import Pyfhel


def _get_param(params: Any, key: str, default: Any = None) -> Any:
    if isinstance(params, dict):
        return params.get(key, default)
    return getattr(params, key, default)


def generate_ckks_context(params) -> Pyfhel:
    scheme = _get_param(params, "scheme", "CKKS")
    poly_modulus_degree = _get_param(params, "poly_modulus_degree")
    coeff_modulus_bits = _get_param(params, "coeff_modulus_bits")
    scale = _get_param(params, "scale")

    if poly_modulus_degree is None:
        raise ValueError("Missing CKKS parameter: poly_modulus_degree")
    if coeff_modulus_bits is None:
        raise ValueError("Missing CKKS parameter: coeff_modulus_bits")
    if scale is None:
        raise ValueError("Missing CKKS parameter: scale")

    he = Pyfhel()
    he.contextGen(
        scheme=scheme,
        n=poly_modulus_degree,
        scale=scale,
        qi_sizes=coeff_modulus_bits,
    )
    return he


DEFAULT_CKKS_PARAMS = {
    "scheme": "CKKS",
    "poly_modulus_degree": 16384,
    "coeff_modulus_bits": [60, 30, 30, 60],
    "scale": 1073741824,
}

CKKS_CONTEXT = generate_ckks_context(DEFAULT_CKKS_PARAMS)