from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import httpx


class ExternalApiError(Exception):
    """Base exception for outbound API integrations."""


class ExternalApiTimeoutError(ExternalApiError):
    pass


class ExternalApiResponseError(ExternalApiError):
    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.details = details or {}


class BaseApiClient:
    """
    Technical base class for outbound HTTP adapters in infrastructure.

    Concrete clients should inherit from this class and implement the methods
    required by domain ports.
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.25,
        default_headers: Mapping[str, str] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._owns_client = client is None
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers=dict(default_headers or {}),
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _get(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("GET", url, params=params, headers=headers)

    async def _post(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("POST", url, json=json, data=data, params=params, headers=headers)

    async def _put(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("PUT", url, json=json, data=data, params=params, headers=headers)

    async def _patch(
        self,
        url: str,
        *,
        json: Any | None = None,
        data: Any | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("PATCH", url, json=json, data=data, params=params, headers=headers)

    async def _delete(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        return await self._request("DELETE", url, params=params, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = await self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.TimeoutException as exc:
                if attempt >= self._max_retries:
                    raise ExternalApiTimeoutError("External API request timed out") from exc
                await self._sleep_before_retry(attempt)
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in {429, 503} and attempt < self._max_retries:
                    await self._sleep_before_retry(attempt)
                else:
                    raise ExternalApiResponseError(
                        message=f"External API returned status {status_code}",
                        status_code=status_code,
                        response_body=exc.response.text,
                    ) from exc
            except httpx.HTTPError as exc:
                raise ExternalApiError(f"External API request failed: {exc}") from exc
            attempt += 1

    @staticmethod
    def parse_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except ValueError as exc:
            raise ExternalApiResponseError(
                message="External API returned an invalid JSON payload",
                status_code=502,
                response_body=response.text,
                details={"reason": "invalid_json"},
            ) from exc

    async def _sleep_before_retry(self, attempt: int) -> None:
        await asyncio.sleep(self._backoff_seconds * (2**attempt))
