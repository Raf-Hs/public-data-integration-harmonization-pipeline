"""Data dictionary generation for the harmonised dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

from .config import DATA_DIR, DOCS_DIR, INDICATORS, COUNTRIES
from .logging_config import configure_logging

logger = configure_logging()

COLUMN_DESCRIPTIONS: Dict[str, str] = {
    "country_iso3": "ISO 3166-1 alpha-3 country code (standardized).",
    "country_iso2": "ISO 3166-1 alpha-2 country code.",
    "country_name": "Standardized country name.",
    "country_type": "Classification: country vs aggregate/territory.",
    "region": "World Bank region.",
    "income_level": "World Bank income classification.",
    "indicator_id": "Original World Bank indicator identifier (preserved).",
    "indicator_name": "Human-readable indicator name.",
    "year": "Calendar year of observation (integer).",
    "value": "Observed numeric value (missing observations are null, not zero).",
    "unit": "Unit of measurement.",
    "source": "Data source identifier.",
    "extracted_at": "UTC timestamp of extraction.",
}


def generate_data_dictionary(df: pd.DataFrame | None = None) -> pd.DataFrame:
    rows: List[Dict[str, str]] = []
    for col, desc in COLUMN_DESCRIPTIONS.items():
        dtype = str(df[col].dtype) if (df is not None and col in df.columns) else ""
        rows.append({"column": col, "data_type": dtype, "description": desc})
    # Indicator entries.
    for ind, info in INDICATORS.items():
        rows.append(
            {
                "column": f"indicator_id={ind}",
                "data_type": "identifier",
                "description": f"{info['name']} | unit: {info['unit']} | {info['description']}",
            }
        )
    # Country entries.
    for code, name in COUNTRIES.items():
        rows.append(
            {
                "column": f"country_iso3={code}",
                "data_type": "identifier",
                "description": f"Country: {name}",
            }
        )
    return pd.DataFrame(rows, columns=["column", "data_type", "description"])


def save_data_dictionary(df: pd.DataFrame | None = None, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or (DATA_DIR / "published")
    out_dir.mkdir(parents=True, exist_ok=True)
    dd = generate_data_dictionary(df)
    path = out_dir / "data_dictionary.csv"
    dd.to_csv(path, index=False)
    logger.info("Data dictionary saved to %s", path)
    # Also write markdown.
    md_path = DOCS_DIR / "DATA_DICTIONARY.md"
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Data Dictionary", "", "| Column | Data Type | Description |", "|---|---|---|"]
    for _, r in dd.iterrows():
        lines.append(f"| {r['column']} | {r['data_type']} | {r['description']} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
