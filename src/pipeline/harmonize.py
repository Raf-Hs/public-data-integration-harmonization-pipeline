"""Harmonization layer: standardize identifiers, names, years, and units."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .config import (
    COUNTRIES,
    INDICATORS,
    ISO2_TO_ISO3,
    REQUIRED_HARMONISED_COLUMNS,
    VALID_COUNTRY_ISO3,
)
from .logging_config import configure_logging

logger = configure_logging()

# Public metadata for the selected countries (source: World Bank country endpoint).
COUNTRY_METADATA: Dict[str, Dict[str, str]] = {
    "MEX": {"region": "Latin America & Caribbean", "income_level": "Upper middle income"},
    "USA": {"region": "North America", "income_level": "High income"},
    "BRA": {"region": "Latin America & Caribbean", "income_level": "Upper middle income"},
    "IND": {"region": "South Asia", "income_level": "Lower middle income"},
    "DEU": {"region": "Europe & Central Asia", "income_level": "High income"},
}


def _standardize_iso3(value: Any) -> str:
    if pd.isna(value):
        return ""
    code = str(value).strip().upper()
    # If an ISO-2 code slipped through, convert.
    if len(code) == 2 and code in ISO2_TO_ISO3:
        return ISO2_TO_ISO3[code]
    return code


def harmonize(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """Standardize cleaned data into the harmonised schema."""
    if cleaned_df.empty:
        return pd.DataFrame(columns=REQUIRED_HARMONISED_COLUMNS)

    df = cleaned_df.copy()

    # Standardize country identifiers to ISO-3.
    df["country_iso3"] = df["country_iso3"].map(_standardize_iso3)
    # Standardize country names from canonical config (source of truth).
    df["country_name"] = df["country_iso3"].map(lambda c: COUNTRIES.get(c, c))

    # Distinguish countries from territories/aggregates.
    df["country_type"] = df["country_iso3"].map(
        lambda c: "country" if c in VALID_COUNTRY_ISO3 else "aggregate_or_territory"
    )

    # Attach public country metadata.
    df["region"] = df["country_iso3"].map(lambda c: COUNTRY_METADATA.get(c, {}).get("region"))
    df["income_level"] = df["country_iso3"].map(
        lambda c: COUNTRY_METADATA.get(c, {}).get("income_level")
    )

    # Standardize year representation (integer).
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    if df["year"].isna().any():
        raise ValueError("Unparseable year encountered during harmonization")

    # Preserve original indicator identifiers; standardize units from config.
    df["unit"] = df["indicator_id"].map(lambda i: INDICATORS.get(str(i), {}).get("unit", ""))

    # Standardize ISO-2 codes from the ISO-3 mapping.
    iso3_to_iso2 = {v: k for k, v in ISO2_TO_ISO3.items()}
    df["country_iso2"] = df["country_iso3"].map(lambda c: iso3_to_iso2.get(c, ""))

    # Source traceability.
    df["source"] = "World Bank Indicators API v2"

    # Reorder to required schema (+ optional metadata columns kept).
    keep = [
        "country_iso3",
        "country_iso2",
        "country_name",
        "country_type",
        "region",
        "income_level",
        "indicator_id",
        "indicator_name",
        "year",
        "value",
        "unit",
        "source",
        "extracted_at",
    ]
    df = df[keep].copy()
    df["year"] = df["year"].astype("int64")
    logger.info("Harmonised %d records", len(df))
    return df
