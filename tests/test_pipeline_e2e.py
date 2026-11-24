"""End-to-end pipeline tests using controlled fixtures (no live API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipeline.api_client import APIResponse
from src.pipeline.config import COUNTRIES, INDICATORS, START_YEAR, END_YEAR
from src.pipeline.pipeline import run_pipeline

FIXTURES = Path(__file__).parent / "fixtures"


def _make_responses():
    template = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    responses = []
    for iso3 in COUNTRIES:
        for ind in INDICATORS:
            data = json.loads(json.dumps(template))
            data["metadata"] = dict(data["metadata"])
            for rec in data["records"]:
                rec["country"] = {"id": iso3[:2], "value": COUNTRIES[iso3]}
                rec["countryiso3code"] = iso3
                rec["indicator"] = {"id": ind, "value": INDICATORS[ind]["name"]}
                rec["value"] = 100.0
            resp = APIResponse(
                endpoint=f"/country/{iso3}/indicator/{ind}",
                params={},
                metadata=data["metadata"],
                records=data["records"],
                extracted_at=data["extracted_at"],
            )
            responses.append(resp)
    return responses


def test_pipeline_e2e_success(tmp_path, monkeypatch):
    # Redirect data dirs to tmp_path to avoid touching repo data
    import src.pipeline.config as cfg
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(cfg, "RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(cfg, "CLEANED_DIR", tmp_path / "data" / "cleaned")
    monkeypatch.setattr(cfg, "HARMONISED_DIR", tmp_path / "data" / "harmonised")
    monkeypatch.setattr(cfg, "PUBLISHED_DIR", tmp_path / "data" / "published")
    monkeypatch.setattr(cfg, "QUALITY_DIR", tmp_path / "data" / "quality")
    # FIGURES_DIR
    monkeypatch.setattr(cfg, "FIGURES_DIR", tmp_path / "reports" / "figures")
    # Re-import modules that cached these constants? They reference cfg attributes at call time mostly.
    # patch in pipeline module namespaces
    import src.pipeline.pipeline as pl
    import src.pipeline.extract as ex
    import src.pipeline.publish as pu
    import src.pipeline.quality as qu
    import src.pipeline.visualize as vi
    import src.pipeline.data_dictionary as dd
    for m in (pl, ex, pu, qu, vi, dd):
        for attr in ("DATA_DIR", "RAW_DIR", "CLEANED_DIR", "HARMONISED_DIR", "PUBLISHED_DIR", "QUALITY_DIR", "FIGURES_DIR", "DOCS_DIR"):
            if hasattr(cfg, attr) and hasattr(m, attr):
                setattr(m, attr, getattr(cfg, attr))

    # patch extract_all to return controlled responses
    monkeypatch.setattr(ex, "extract_all", lambda client=None, run_id=None, save_raw=True: _make_responses())

    # patch FIGURES_DIR in visualize already
    summary = run_pipeline(client=None, run_id="testrun")
    assert summary["passed"] is True
    assert summary["countries"] == 5
    assert summary["indicators"] == 5
    assert summary["harmonised_records"] == 250
    assert "csv" in summary["outputs"]
    assert Path(summary["outputs"]["csv"]).exists()


def test_pipeline_quality_gate_blocks_publication(tmp_path, monkeypatch):
    # Force a quality failure by monkeypatching run_quality_checks to return failed report
    import src.pipeline.config as cfg
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(cfg, "RAW_DIR", tmp_path / "data" / "raw")
    monkeypatch.setattr(cfg, "CLEANED_DIR", tmp_path / "data" / "cleaned")
    monkeypatch.setattr(cfg, "HARMONISED_DIR", tmp_path / "data" / "harmonised")
    monkeypatch.setattr(cfg, "PUBLISHED_DIR", tmp_path / "data" / "published")
    monkeypatch.setattr(cfg, "QUALITY_DIR", tmp_path / "data" / "quality")
    monkeypatch.setattr(cfg, "FIGURES_DIR", tmp_path / "reports" / "figures")

    import src.pipeline.pipeline as pl
    import src.pipeline.extract as ex
    import src.pipeline.publish as pu
    import src.pipeline.quality as qu
    import src.pipeline.visualize as vi
    import src.pipeline.data_dictionary as dd
    for m in (pl, ex, pu, qu, vi, dd):
        for attr in ("DATA_DIR", "RAW_DIR", "CLEANED_DIR", "HARMONISED_DIR", "PUBLISHED_DIR", "QUALITY_DIR", "FIGURES_DIR", "DOCS_DIR"):
            if hasattr(cfg, attr) and hasattr(m, attr):
                setattr(m, attr, getattr(cfg, attr))

    monkeypatch.setattr(ex, "extract_all", lambda client=None, run_id=None, save_raw=True: _make_responses())

    from src.pipeline.quality import QualityReport
    failed_report = QualityReport(generated_at="now", total_records=1, errors=[{"check": "x", "message": "fail"}])
    monkeypatch.setattr(pl, "run_quality_checks", lambda df: failed_report)

    summary = run_pipeline(client=None, run_id="testrun2")
    assert summary["passed"] is False
    assert summary["outputs"] == {}
