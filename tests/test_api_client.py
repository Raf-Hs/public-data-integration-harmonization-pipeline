"""Tests for the World Bank API client (using controlled fixtures)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipeline.api_client import WorldBankClient, APIResponse


FIXTURES = Path(__file__).parent / "fixtures"


def test_api_response_parsing_shape():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    assert "records" in data
    assert "metadata" in data
    assert len(data["records"]) == 10
    rec = data["records"][0]
    assert rec["countryiso3code"] == "MEX"
    assert rec["indicator"]["id"] == "SP.POP.TOTL"


def test_api_response_dataclass_construction():
    data = json.loads((FIXTURES / "mex_population.json").read_text(encoding="utf-8"))
    resp = APIResponse(
        endpoint="/country/MEX/indicator/SP.POP.TOTL",
        params={},
        metadata=data["metadata"],
        records=data["records"],
        extracted_at=data["extracted_at"],
    )
    assert len(resp.records) == 10
    assert resp.metadata["total"] == 10
