import requests
from requests.exceptions import RequestException, Timeout

from .errors import APIError, ConnectionError


class API:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get(self, path: str):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Timeout as exc:
            raise ConnectionError(f"GET request to {url} timed out") from exc
        except RequestException as exc:
            status_code = getattr(exc.response, "status_code", 0) or 0
            details = None
            if exc.response is not None:
                try:
                    details = exc.response.json()
                except ValueError:
                    details = {"raw": exc.response.text}
            raise APIError(
                status_code=status_code,
                message=f"GET request to {url} failed",
                details=details,
            ) from exc

    def post(self, path: str, data=None, json=None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.post(
                url,
                data=data,
                json=json,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except Timeout as exc:
            raise ConnectionError(f"POST request to {url} timed out") from exc
        except RequestException as exc:
            status_code = getattr(exc.response, "status_code", 0) or 0
            details = None
            if exc.response is not None:
                try:
                    details = exc.response.json()
                except ValueError:
                    details = {"raw": exc.response.text}
            raise APIError(
                status_code=status_code,
                message=f"POST request to {url} failed",
                details=details,
            ) from exc