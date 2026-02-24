"""
- Transport errors
- Schema validation failures
- Server-declared protocol errors
- Job lifecycle failures
- Crypto/session issues
"""

from typing import Optional


# Base Error
class HEAPIClientError(Exception):
    """Base class for all client-side SDK errors."""
    pass


# Transport / HTTP Errors
class APIError(HEAPIClientError):
    """
    Raised when the API returns a non-success HTTP response.
    """

    def __init__(self, status_code: int, message: str, details: Optional[dict] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"[HTTP {status_code}] {message}")


class ConnectionError(HEAPIClientError):
    """
    Raised when the client cannot reach the server.
    """
    pass


# Schema / Protocol Errors
class SchemaValidationError(HEAPIClientError):
    """
    Raised when a request or response fails JSON Schema validation.
    """

    def __init__(self, message: str, payload: Optional[dict] = None):
        self.payload = payload
        super().__init__(message)


class ProtocolError(HEAPIClientError):
    """
    Raised when the server returns a protocol-level error
    (valid HTTP, but application-level failure).
    """

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"[{code}] {message}")


# Job Lifecycle Errors
class JobFailedError(HEAPIClientError):
    """
    Raised when a job reaches 'failed' status.
    """

    def __init__(self, job_id: str, reason: Optional[str] = None):
        self.job_id = job_id
        self.reason = reason
        msg = f"Job '{job_id}' failed."
        if reason:
            msg += f" Reason: {reason}"
        super().__init__(msg)


class JobTimeoutError(HEAPIClientError):
    """
    Raised when polling exceeds allowed timeout.
    """
    pass


# Crypto / Session Errors
class CryptoError(HEAPIClientError):
    """
    Raised for encryption, decryption, or session failures.
    """
    pass


# Protocol Error Mapping Helper
def map_protocol_error(error_payload: dict) -> HEAPIClientError:
    """
    Convert a server-declared protocol error payload
    into a structured client-side exception.

    Expected server error shape:
    {
        "error": {
            "code": "INVALID_CIPHERTEXT",
            "message": "Scale mismatch"
        }
    }
    """

    if not isinstance(error_payload, dict):
        return ProtocolError("UNKNOWN_ERROR", "Malformed error response")

    error_obj = error_payload.get("error", {})
    code = error_obj.get("code", "UNKNOWN_ERROR")
    message = error_obj.get("message", "Unknown error")

    # Map specific protocol codes to typed exceptions
    if code in {"INVALID_SCHEMA", "SCHEMA_VALIDATION_FAILED"}:
        return SchemaValidationError(message)

    if code in {"INVALID_CIPHERTEXT", "CRYPTO_POLICY_VIOLATION"}:
        return CryptoError(message)

    if code in {"JOB_FAILED"}:
        return JobFailedError(job_id="unknown", reason=message)

    # Default fallback
    return ProtocolError(code, message)