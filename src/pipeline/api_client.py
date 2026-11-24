"""World Bank API client with pagination, retries, and error handling."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from .config import (
    MAX_RETRIES,
    RETRY_BACKOFF_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    WORLD_BANK_BASE_URL,
)
from .logging_config import configure_logging

logger = configure_logging()


@dataclass
class APIResponse:
    """Wrapper around a World Bank API response."""

    endpoint: str
    params: Dict[str, Any]
    metadata: Dict[str, Any]
    records: List[Dict[str, Any]]
    extracted_at: str
    raw_payload: Any = None


class WorldBankAPIError(Exception):
    """Raised when the World Bank API returns an error or unexpected payload."""


class WorldBankClient:
    """HTTP client for the World Bank Indicators API."""

    def __init__(
        self,
        base_url: str = WORLD_BANK_BASE_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "public-data-pipeline/1.0"})

    def _request(self, url: str, params: Dict[str, Any]) -> Any:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict) and "message" in payload:
                    raise WorldBankAPIError(f"API error: {payload['message']}")
                if not isinstance(payload, list) or len(payload) < 2:
                    raise WorldBankAPIError(f"Unexpected API payload: {payload!r}")
                return payload
            except (requests.RequestException, ValueError, WorldBankAPIError) as exc:
                last_exc = exc
                logger.warning("Request failed (attempt %d/%d): %s", attempt, self.max_retries, exc)
                if attempt < self.max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise WorldBankAPIError(f"Request failed after {self.max_retries} attempts: {last_exc}")

    def get_country_metadata(self, country_code: str) -> Dict[str, Any]:
        """Fetch metadata for a single country (ISO-2 or ISO-3)."""
        url = f"{self.base_url}/country/{country_code}"
        params = {"format": "json"}
        payload = self._request(url, params)
        records = payload[1] or []
        if not records:
            raise WorldBankAPIError(f"No metadata returned for country {country_code}")
        return records[0]

    def get_indicator_data(
        self,
        country_code: str,
        indicator_id: str,
        start_year: int,
        end_year: int,
        per_page: int = 100,
    ) -> APIResponse:
        """Fetch indicator observations for a country with full pagination."""
        endpoint = f"/country/{country_code}/indicator/{indicator_id}"
        url = f"{self.base_url}{endpoint}"
        all_records: List[Dict[str, Any]] = []
        page = 1
        pages = 1
        metadata: Dict[str, Any] = {}
        extracted_at = datetime.now(timezone.utc).isoformat()

        while page <= pages:
            params = {
                "format": "json",
                "date": f"{start_year}:{end_year}",
                "per_page": per_page,
                "page": page,
            }
            payload = self._request(url, params)
            page_meta = payload[0] or {}
            metadata = page_meta
            pages = int(page_meta.get("pages", 1) or 1)
            records = payload[1] or []
            all_records.extend(records)
            page += 1
            if page > pages:
                break

        return APIResponse(
            endpoint=endpoint,
            params={"country": country_code, "indicator": indicator_id, "date": f"{start_year}:{end_year}"},
            metadata=metadata,
            records=all_records,
            extracted_at=extracted_at,
            raw_payload={"metadata": metadata, "records": all_records},
        )
