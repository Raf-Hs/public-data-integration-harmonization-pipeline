"""Data quality framework: structural, completeness, uniqueness, validity, consistency, time-series checks."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from .config import (
    COUNTRIES,
    INDICATORS,
    QUALITY_DIR,
    START_YEAR,
    END_YEAR,
    VALID_COUNTRY_ISO3,
    VALID_INDICATOR_IDS,
    VALID_YEARS,
)
from .logging_config import configure_logging

logger = configure_logging()


@dataclass
class QualityReport:
    generated_at: str
    total_records: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    info: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_records": self.total_records,
            "passed": self.passed,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


def _add(report: QualityReport, level: str, check: str, message: str, details: Any = None) -> None:
    entry = {"check": check, "message": message}
    if details is not None:
        entry["details"] = details
    getattr(report, level).append(entry)


def run_quality_checks(df: pd.DataFrame, expected_years: range = range(START_YEAR, END_YEAR + 1)) -> QualityReport:
    """Run all quality checks and return a QualityReport."""
    report = QualityReport(generated_at=datetime.now(timezone.utc).isoformat(), total_records=len(df))

    required_columns = [
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

    # --- Structural checks ---
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        _add(report, "errors", "structural.required_columns", f"Missing required columns: {missing_cols}")
    else:
        _add(report, "info", "structural.required_columns", "All required columns present.")

    if "year" in df.columns:
        if not pd.api.types.is_integer_dtype(df["year"]):
            # allow nullable int
            if not str(df["year"].dtype).startswith("Int") and not pd.api.types.is_integer_dtype(df["year"]):
                _add(report, "errors", "structural.year_type", f"Year column is not integer: {df['year'].dtype}")
        # range check
        out_of_range = df.loc[~df["year"].isin(VALID_YEARS), "year"] if "year" in df.columns else pd.Series(dtype=int)
        if len(out_of_range) > 0:
            _add(report, "errors", "structural.year_range", f"Years outside {START_YEAR}-{END_YEAR}: {sorted(set(out_of_range.tolist()))}")

    # --- Completeness checks ---
    for col in ["country_iso3", "indicator_id", "year"]:
        if col in df.columns:
            missing = int(df[col].isna().sum())
            if missing > 0:
                _add(report, "errors", f"completeness.{col}", f"{missing} missing values in required field '{col}'.")
            else:
                _add(report, "info", f"completeness.{col}", f"No missing values in '{col}'.")

    # missing values in 'value' are observations, not errors.
    if "value" in df.columns:
        missing_values = int(df["value"].isna().sum())
        _add(
            report,
            "info",
            "completeness.value",
            f"{missing_values} missing observations (value is null).",
            {"missing_observations": missing_values},
        )

    # --- Uniqueness checks ---
    if all(c in df.columns for c in ["country_iso3", "indicator_id", "year"]):
        dupes = df.duplicated(subset=["country_iso3", "indicator_id", "year"])
        n_dupes = int(dupes.sum())
        if n_dupes > 0:
            _add(report, "errors", "uniqueness.duplicates", f"{n_dupes} duplicate country-indicator-year records.")
        else:
            _add(report, "info", "uniqueness.duplicates", "No duplicate country-indicator-year records.")

    # --- Validity checks ---
    if "country_iso3" in df.columns:
        invalid_countries = sorted(set(df.loc[~df["country_iso3"].isin(VALID_COUNTRY_ISO3), "country_iso3"].astype(str).tolist()))
        if invalid_countries:
            _add(report, "errors", "validity.country", f"Invalid country identifiers: {invalid_countries}")
        else:
            _add(report, "info", "validity.country", "All country identifiers valid.")

    if "indicator_id" in df.columns:
        invalid_inds = sorted(set(df.loc[~df["indicator_id"].isin(VALID_INDICATOR_IDS), "indicator_id"].astype(str).tolist()))
        if invalid_inds:
            _add(report, "errors", "validity.indicator", f"Invalid indicator identifiers: {invalid_inds}")
        else:
            _add(report, "info", "validity.indicator", "All indicator identifiers valid.")

    if "value" in df.columns:
        # numeric check: non-null values must be numeric (already coerced); detect rows where raw was non-numeric?
        # Check for non-finite values.
        import numpy as np

        try:
            inf_count = int(np.isinf(df["value"].astype(float)).sum())
        except Exception:
            inf_count = 0
        if inf_count > 0:
            _add(report, "errors", "validity.numeric", f"{inf_count} non-finite numeric values.")

    # Reasonable year already checked.

    # --- Consistency checks ---
    if "unit" in df.columns and "indicator_id" in df.columns:
        inconsistent = []
        for ind, grp in df.groupby("indicator_id"):
            units = set(str(u) for u in grp["unit"].dropna().unique())
            expected = INDICATORS.get(str(ind), {}).get("unit")
            if expected is not None and units and units != {expected}:
                inconsistent.append({"indicator": ind, "units": sorted(units), "expected": expected})
        if inconsistent:
            _add(report, "errors", "consistency.units", f"Inconsistent units detected: {inconsistent}")
        else:
            _add(report, "info", "consistency.units", "Units consistent per indicator.")

    if "country_iso3" in df.columns:
        # consistent code format: 3 uppercase letters.
        bad = df.loc[~df["country_iso3"].astype(str).str.match(r"^[A-Z]{3}$"), "country_iso3"]
        if len(bad) > 0:
            _add(report, "warnings", "consistency.country_code_format", f"Non-standard country codes: {sorted(set(bad.astype(str)))}")

    # --- Time-series checks ---
    # Missing historical observations per country-indicator.
    if all(c in df.columns for c in ["country_iso3", "indicator_id", "year"]):
        expected = set(expected_years)
        missing_obs = []
        for (country, ind), grp in df.groupby(["country_iso3", "indicator_id"]):
            present = set(grp["year"].tolist())
            gaps = sorted(expected - present)
            if gaps:
                missing_obs.append({"country": country, "indicator": ind, "missing_years": gaps})
        if missing_obs:
            _add(
                report,
                "warnings",
                "timeseries.missing_observations",
                f"{len(missing_obs)} country-indicator series have missing years.",
                {"series": missing_obs},
            )
        else:
            _add(report, "info", "timeseries.missing_observations", "No missing years in any series.")

        # Unexpected gaps (already captured above) + unusual value changes.
        unusual = []
        for (country, ind), grp in df.groupby(["country_iso3", "indicator_id"]):
            g = grp.sort_values("year")
            vals = g["value"].astype(float)
            for i in range(1, len(vals)):
                prev = vals.iloc[i - 1]
                cur = vals.iloc[i]
                if pd.isna(prev) or pd.isna(cur) or prev == 0:
                    continue
                pct = abs((cur - prev) / prev)
                if pct > 0.5:
                    unusual.append(
                        {
                            "country": country,
                            "indicator": ind,
                            "year": int(g["year"].iloc[i]),
                            "change_pct": round(float(pct) * 100, 2),
                        }
                    )
        if unusual:
            _add(
                report,
                "warnings",
                "timeseries.unusual_changes",
                f"{len(unusual)} year-over-year changes exceed 50%.",
                {"changes": unusual},
            )
        else:
            _add(report, "info", "timeseries.unusual_changes", "No unusual year-over-year changes detected.")

    # Coverage summary info.
    if not df.empty:
        coverage = (
            df.groupby(["country_iso3", "indicator_id"]).size().reset_index(name="n_obs")
        )
        _add(
            report,
            "info",
            "coverage.summary",
            f"{df['country_iso3'].nunique()} countries x {df['indicator_id'].nunique()} indicators.",
            {"rows": coverage.to_dict(orient="records")},
        )

    return report


def save_quality_report(report: QualityReport, path: Path | None = None) -> Path:
    path = path or (QUALITY_DIR / "quality_report.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(report.to_dict(), fh, indent=2, ensure_ascii=False)
    logger.info("Quality report saved to %s (passed=%s)", path, report.passed)
    return path
