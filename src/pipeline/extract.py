"""Extraction layer: retrieve and preserve raw World Bank data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .api_client import WorldBankClient, APIResponse
from .config import (
    COUNTRIES,
    INDICATORS,
    RAW_DIR,
    START_YEAR,
    END_YEAR,
)
from .logging_config import configure_logging

logger = configure_logging()


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def extract_all(
    client: WorldBankClient | None = None,
    run_id: str | None = None,
    save_raw: bool = True,
) -> List[APIResponse]:
    """Extract indicator data for all configured countries and indicators.

    Returns a list of APIResponse objects (one per country/indicator).
    """
    client = client or WorldBankClient()
    run_id = run_id or _run_id()
    run_dir = RAW_DIR / run_id
    if save_raw:
        run_dir.mkdir(parents=True, exist_ok=True)

    responses: List[APIResponse] = []
    total = len(COUNTRIES) * len(INDICATORS)
    done = 0
    for iso3, country_name in COUNTRIES.items():
        # World Bank country endpoint accepts ISO-3 codes directly.
        for indicator_id in INDICATORS:
            logger.info("Extracting %s / %s", iso3, indicator_id)
            resp = client.get_indicator_data(
                country_code=iso3,
                indicator_id=indicator_id,
                start_year=START_YEAR,
                end_year=END_YEAR,
            )
            responses.append(resp)
            if save_raw:
                out_file = run_dir / f"{iso3}_{indicator_id}.json"
                with out_file.open("w", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "endpoint": resp.endpoint,
                            "params": resp.params,
                            "metadata": resp.metadata,
                            "extracted_at": resp.extracted_at,
                            "records": resp.records,
                        },
                        fh,
                        indent=2,
                        ensure_ascii=False,
                    )
            done += 1
            logger.info("Progress %d/%d", done, total)

    # Persist country metadata once per run.
    if save_raw:
        meta = {}
        for iso3 in COUNTRIES:
            try:
                meta[iso3] = client.get_country_metadata(iso3)
            except Exception as exc:  # pragma: no cover - network
                logger.warning("Could not fetch metadata for %s: %s", iso3, exc)
        with (run_dir / "country_metadata.json").open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)

    logger.info("Extraction complete: %d responses", len(responses))
    return responses
