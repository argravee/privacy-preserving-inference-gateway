from Pyfhel import PyCtxt

from heapi_client.errors import CryptoError


def serialize_ciphertext(ct) -> dict:
    try:
        return {
            "encoding": "hex",
            "payload": ct.to_bytes().hex(),
        }
    except Exception as exc:
        raise CryptoError(f"Failed to serialize ciphertext: {exc}") from exc


def deserialize_ciphertext(he, payload: str):
    if not isinstance(payload, str):
        raise CryptoError("Ciphertext payload must be a string")

    try:
        ct_bytes = bytes.fromhex(payload)
    except ValueError as exc:
        raise CryptoError("Ciphertext payload is not valid hex") from exc

    try:
        if hasattr(he, "from_bytes_ciphertext"):
            return he.from_bytes_ciphertext(ct_bytes)
        return PyCtxt(pyfhel=he, bytestring=ct_bytes)
    except Exception as exc:
        raise CryptoError(f"Failed to deserialize ciphertext: {exc}") from exc