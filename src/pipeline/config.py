"""Central configuration for the data pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

# Project root resolved from this file location.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
HARMONISED_DIR = DATA_DIR / "harmonised"
PUBLISHED_DIR = DATA_DIR / "published"
QUALITY_DIR = DATA_DIR / "quality"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
SQL_DIR = PROJECT_ROOT / "sql"
DOCS_DIR = PROJECT_ROOT / "docs"

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"
REQUEST_TIMEOUT_SECONDS = 60
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 2
DEFAULT_PER_PAGE = 100

# Historical window.
START_YEAR = 2015
END_YEAR = 2024

# Countries of interest (ISO-3 codes). All are UN member states.
COUNTRIES: Dict[str, str] = {
    "MEX": "Mexico",
    "USA": "United States",
    "BRA": "Brazil",
    "IND": "India",
    "DEU": "Germany",
}

# Indicators of interest. Unit labels are assigned here because the
# World Bank API frequently returns an empty "unit" field.
INDICATORS: Dict[str, Dict[str, str]] = {
    "SP.POP.TOTL": {
        "name": "Population, total",
        "unit": "People",
        "description": "Total population based on the de facto definition of population.",
    },
    "NY.GDP.PCAP.CD": {
        "name": "GDP per capita (current US$)",
        "unit": "Current US$",
        "description": "Gross domestic product divided by midyear population.",
    },
    "SP.DYN.LE00.IN": {
        "name": "Life expectancy at birth, total (years)",
        "unit": "Years",
        "description": "Number of years a newborn infant would live if prevailing mortality patterns persist.",
    },
    "SL.UEM.TOTL.ZS": {
        "name": "Unemployment, total (% of total labor force)",
        "unit": "Percentage",
        "description": "Share of the labor force without work but available for and seeking employment (modeled ILO estimate).",
    },
    "EG.ELC.ACCS.ZS": {
        "name": "Access to electricity (% of population)",
        "unit": "Percentage",
        "description": "Percentage of population with access to electricity.",
    },
}

# ISO-2 to ISO-3 mapping for the selected countries (used during harmonization).
ISO2_TO_ISO3 = {
    "MX": "MEX",
    "US": "USA",
    "BR": "BRA",
    "IN": "IND",
    "DE": "DEU",
}

REQUIRED_CLEANED_COLUMNS = [
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

REQUIRED_HARMONISED_COLUMNS = [
    "country_iso3",
    "country_iso2",
    "country_name",
    "country_type",
    "indicator_id",
    "indicator_name",
    "year",
    "value",
    "unit",
    "source",
    "extracted_at",
]

VALID_COUNTRY_ISO3 = set(COUNTRIES.keys())
VALID_INDICATOR_IDS = set(INDICATORS.keys())
VALID_YEARS = set(range(START_YEAR, END_YEAR + 1))