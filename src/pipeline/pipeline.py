"""End-to-end pipeline orchestration: RAW -> CLEANED -> HARMONISED -> VALIDATED -> PUBLISHED."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .api_client import WorldBankClient
from .config import (
    CLEANED_DIR,
    HARMONISED_DIR,
    PROJECT_ROOT,
    PUBLISHED_DIR,
    QUALITY_DIR,
)
from .data_dictionary import save_data_dictionary
from .extract import extract_all
from .harmonize import harmonize
from .logging_config import configure_logging
from .publish import publish_all
from .quality import run_quality_checks, save_quality_report
from .transform import clean
from .visualize import generate_all_charts

logger = configure_logging()


def run_pipeline(client: Any = None, run_id: str | None = None) -> Dict[str, Any]:
    """Execute the full pipeline and return a summary dict."""
    client = client or WorldBankClient()

    # Layer 1 - RAW
    logger.info("=== LAYER 1: RAW extraction ===")
    responses = extract_all(client=client, run_id=run_id, save_raw=True)

    # Layer 2 - CLEANED
    logger.info("=== LAYER 2: CLEANING ===")
    cleaned_df, invalid_records = clean(responses)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_path = CLEANED_DIR / "cleaned_dataset.csv"
    cleaned_df.to_csv(cleaned_path, index=False)
    # save invalid records for traceability
    with (CLEANED_DIR / "invalid_records.json").open("w", encoding="utf-8") as fh:
        json.dump(invalid_records, fh, indent=2, default=str)

    # Layer 3 - HARMONISED
    logger.info("=== LAYER 3: HARMONIZATION ===")
    harmonised_df = harmonize(cleaned_df)
    HARMONISED_DIR.mkdir(parents=True, exist_ok=True)
    harmonised_path = HARMONISED_DIR / "harmonised_dataset.csv"
    harmonised_df.to_csv(harmonised_path, index=False)
    harmonised_df.to_parquet(HARMONISED_DIR / "harmonised_dataset.parquet", index=False)

    # Quality
    logger.info("=== QUALITY CHECKS ===")
    report = run_quality_checks(harmonised_df)
    save_quality_report(report)
    if not report.passed:
        logger.error("Quality gate FAILED; publication blocked.")
        # still generate charts? skip publication
        return {
            "passed": False,
            "records_extracted": sum(len(r.records) for r in responses),
            "cleaned_records": len(cleaned_df),
            "harmonised_records": len(harmonised_df),
            "invalid_records": len(invalid_records),
            "quality_report": report.to_dict(),
            "outputs": {},
        }

    # Layer 4 - PUBLISHED
    logger.info("=== LAYER 4: PUBLICATION ===")
    outputs = publish_all(harmonised_df, quality_passed=True)
    save_data_dictionary(harmonised_df)

    # Visualizations
    logger.info("=== VISUALIZATIONS ===")
    chart_paths = generate_all_charts(harmonised_df, report.to_dict())
    chart_paths = [str(Path(p).relative_to(PROJECT_ROOT)) if Path(p).is_absolute() and PROJECT_ROOT in Path(p).parents else str(p) for p in chart_paths]

    summary = {
        "passed": True,
        "records_extracted": sum(len(r.records) for r in responses),
        "cleaned_records": len(cleaned_df),
        "harmonised_records": len(harmonised_df),
        "invalid_records": len(invalid_records),
        "missing_observations": int(harmonised_df["value"].isna().sum()),
        "countries": harmonised_df["country_iso3"].nunique(),
        "indicators": harmonised_df["indicator_id"].nunique(),
        "quality_report": report.to_dict(),
        "outputs": {k: str(Path(v).relative_to(PROJECT_ROOT)) if Path(v).is_absolute() and PROJECT_ROOT in Path(v).parents else str(v) for k, v in outputs.items()},
        "charts": chart_paths,
    }
    # Save summary
    (PUBLISHED_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    logger.info("Pipeline complete. Summary saved.")
    return summary


if __name__ == "__main__":
    run_pipeline()
