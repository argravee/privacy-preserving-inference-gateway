from __future__ import annotations

from typing import List

from Pyfhel import Pyfhel

from ..errors import CryptoError, SchemaValidationError
from .wire import deserialize_ciphertext, serialize_ciphertext


class CKKS_Session:
    """
    Client-side CKKS cryptographic session.

    Owns:
    - context
    - secret key
    - encryption
    - decryption
    """

    def __init__(
            self,
            poly_modulus_degree: int = 8192,
            coeff_modulus_bits: List[int] = [60, 40, 40, 60],
            scale: float = 2**40,
    ):
        try:
            self.he = Pyfhel()
            self.he.contextGen(
                scheme="CKKS",
                n=poly_modulus_degree,
                qi_sizes=coeff_modulus_bits,
                scale=scale,
            )
            self.he.keyGen()
        except Exception as exc:
            raise CryptoError(f"Failed to initialize CKKS session: {exc}") from exc

    def encrypt(self, values: List[float]) -> dict:
        try:
            ct = self.he.encryptFrac(values)
            return serialize_ciphertext(ct)
        except Exception as exc:
            raise CryptoError(f"Encryption failed: {exc}") from exc

    def decrypt(self, response: dict):
        if "payload" not in response:
            raise SchemaValidationError(
                "Inference response missing 'payload' field",
                payload=response,
            )

        try:
            ct = deserialize_ciphertext(self.he, response["payload"])
            return self.he.decryptFrac(ct)
        except Exception as exc:
            raise CryptoError(f"Decryption failed: {exc}") from exc

    @classmethod
    def from_model(cls, model_metadata: dict):
        """
        Create CKKS session from discovered model metadata.
        Expected model shape includes:
        - he_scheme
        - encryption_parameters
        """
        scheme = model_metadata.get("he_scheme")
        if scheme != "CKKS":
            raise CryptoError(f"Unsupported HE scheme: {scheme}")

        params = model_metadata.get("encryption_parameters")
        if not isinstance(params, dict):
            raise CryptoError("Model metadata missing encryption_parameters")

        required_fields = (
            "poly_modulus_degree",
            "coeff_modulus_bits",
            "scale",
        )
        missing = [field for field in required_fields if field not in params]
        if missing:
            raise CryptoError(
                f"encryption_parameters missing required fields: {', '.join(missing)}"
            )

        poly_modulus_degree = params["poly_modulus_degree"]
        coeff_modulus_bits = params["coeff_modulus_bits"]
        scale = params["scale"]

        if not isinstance(poly_modulus_degree, int):
            raise CryptoError("poly_modulus_degree must be an integer")
        if not isinstance(coeff_modulus_bits, list) or not all(
                isinstance(x, int) for x in coeff_modulus_bits
        ):
            raise CryptoError("coeff_modulus_bits must be a list of integers")
        if not isinstance(scale, (int, float)):
            raise CryptoError("scale must be numeric")

        return cls(
            poly_modulus_degree=poly_modulus_degree,
            coeff_modulus_bits=coeff_modulus_bits,
            scale=scale,
        )