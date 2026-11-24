"""Cleaning layer: normalize raw World Bank responses into consistent tabular form."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import pandas as pd

from .config import INDICATORS, REQUIRED_CLEANED_COLUMNS
from .logging_config import configure_logging

logger = configure_logging()


def _standardize_missing(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "" or stripped.lower() in {"null", "none", "nan", "n/a"}:
            return None
        return stripped
    return value


def flatten_responses(responses: List[Any]) -> List[Dict[str, Any]]:
    """Flatten API responses into a list of raw record dictionaries."""
    rows: List[Dict[str, Any]] = []
    for resp in responses:
        metadata = getattr(resp, "metadata", {}) or {}
        extracted_at = getattr(resp, "extracted_at", datetime.now(timezone.utc).isoformat())
        last_updated = metadata.get("lastupdated")
        records = getattr(resp, "records", None)
        if records is None and isinstance(resp, dict):
            records = resp.get("records", [])
            metadata = resp.get("metadata", metadata)
            extracted_at = resp.get("extracted_at", extracted_at)
            last_updated = metadata.get("lastupdated", last_updated)
        for rec in records or []:
            rows.append(
                {
                    "country_iso2": _standardize_missing((rec.get("country") or {}).get("id")),
                    "country_name_raw": _standardize_missing((rec.get("country") or {}).get("value")),
                    "country_iso3_raw": _standardize_missing(rec.get("countryiso3code")),
                    "indicator_id": _standardize_missing((rec.get("indicator") or {}).get("id")),
                    "indicator_name_raw": _standardize_missing((rec.get("indicator") or {}).get("value")),
                    "year_raw": _standardize_missing(rec.get("date")),
                    "value_raw": _standardize_missing(rec.get("value")),
                    "unit_raw": _standardize_missing(rec.get("unit")),
                    "obs_status": _standardize_missing(rec.get("obs_status")),
                    "decimal": rec.get("decimal"),
                    "source_last_updated": last_updated,
                    "extracted_at": extracted_at,
                }
            )
    return rows


def clean(responses: List[Any]) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Clean raw responses into a structurally consistent DataFrame.

    Returns (cleaned_df, invalid_records). Invalid records are never silently
    dropped; they are returned for inspection and logged.
    """
    rows = flatten_responses(responses)
    if not rows:
        return pd.DataFrame(columns=REQUIRED_CLEANED_COLUMNS), []

    df = pd.DataFrame(rows)

    # Normalize column names already snake_case.
    # Convert year to numeric (coerce invalid to NaN for detection).
    df["year"] = pd.to_numeric(df["year_raw"], errors="coerce")
    # Convert value to numeric.
    df["value"] = pd.to_numeric(df["value_raw"], errors="coerce")

    # Standardize country iso3: prefer provided iso3 code, uppercase.
    df["country_iso3"] = df["country_iso3_raw"].astype("string").str.strip().str.upper()
    # If missing, fall back to iso2 mapping later in harmonize; keep NaN.

    # Indicator name: prefer config canonical name.
    df["indicator_name"] = df["indicator_id"].map(
        lambda x: _indicator_name(x) if pd.notna(x) else None
    )
    # Fall back to raw name when config missing.
    mask = df["indicator_name"].isna()
    df.loc[mask, "indicator_name"] = df.loc[mask, "indicator_name_raw"]

    # Unit: prefer config canonical unit, fall back to raw.
    df["unit"] = df["indicator_id"].map(lambda x: _indicator_unit(x) if pd.notna(x) else None)
    mask = df["unit"].isna() | (df["unit"].astype("string").str.strip() == "")
    df.loc[mask, "unit"] = df.loc[mask, "unit_raw"]

    # Country name cleaned (strip).
    df["country_name"] = df["country_name_raw"].astype("string").str.strip()

    # decimal to nullable int.
    df["decimal"] = pd.to_numeric(df["decimal"], errors="coerce")

    # Detect invalid records (required fields missing or unparseable).
    invalid_mask = (
        df["country_iso2"].isna()
        | df["indicator_id"].isna()
        | df["year"].isna()
        | df["country_iso3"].isna()
    )
    invalid_records = df[invalid_mask].to_dict(orient="records")

    if invalid_records:
        logger.warning("Detected %d invalid records during cleaning", len(invalid_records))

    # Drop invalid records from cleaned output but report them.
    cleaned = df.loc[~invalid_mask].copy()

    # Deduplicate exact duplicate rows, keeping first.
    before = len(cleaned)
    cleaned = cleaned.drop_duplicates(
        subset=["country_iso3", "indicator_id", "year"], keep="first"
    )
    dropped = before - len(cleaned)
    if dropped:
        logger.warning("Dropped %d duplicate records", dropped)

    # Final column selection.
    cleaned = cleaned[
        [
            "country_iso2",
            "country_iso3",
            "country_name",
            "indicator_id",
            "indicator_name",
            "year",
            "value",
            "unit",
            "obs_status",
            "decimal",
            "source_last_updated",
            "extracted_at",
        ]
    ].copy()

    # Ensure types.
    cleaned["year"] = cleaned["year"].astype("int64")
    cleaned["country_iso2"] = cleaned["country_iso2"].astype("string")
    cleaned["country_iso3"] = cleaned["country_iso3"].astype("string")
    cleaned["country_name"] = cleaned["country_name"].astype("string")
    cleaned["indicator_id"] = cleaned["indicator_id"].astype("string")
    cleaned["indicator_name"] = cleaned["indicator_name"].astype("string")
    cleaned["unit"] = cleaned["unit"].astype("string")
    cleaned["obs_status"] = cleaned["obs_status"].astype("string")
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")

    # Rename to match required schema exactly.
    cleaned = cleaned.rename(columns={})
    assert list(cleaned.columns) == REQUIRED_CLEANED_COLUMNS, cleaned.columns.tolist()

    logger.info("Cleaned %d records", len(cleaned))
    return cleaned, invalid_records


def _indicator_name(indicator_id: Any) -> str | None:
    from .config import INDICATORS

    info = INDICATORS.get(str(indicator_id))
    return info["name"] if info else None


def _indicator_unit(indicator_id: Any) -> str | None:
    from .config import INDICATORS

    info = INDICATORS.get(str(indicator_id))
    return info["unit"] if info else None
