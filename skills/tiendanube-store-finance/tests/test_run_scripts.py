import json
from workbook import parse_workbook
from financials import build_financials
from adapters import to_forecast_input
from run_scripts import run_script
from ratios_filter import SURFACED_CATEGORIES, filter_ratios

def test_run_forecast_returns_json(fixture_workbook, tmp_path):
    fin = build_financials(parse_workbook(fixture_workbook))
    inp = to_forecast_input(fin, {"forecastPeriods": 6})
    out = run_script("forecast_builder.py", inp, tmp_path)
    assert isinstance(out, dict)  # parsed JSON, not a crash

def test_filter_ratios_keeps_surfaced_drops_leverage_and_insufficient():
    raw = {"categories": {
        "profitability": {"gross_margin": {"value": 0.6, "interpretation": "ok"}},
        "liquidity": {"current_ratio": {"value": 2.0, "interpretation": "ok"}},
        "leverage": {"debt_to_equity": {"value": 9, "interpretation": "ok"}},
        "valuation": {"pe_ratio": {"value": 12, "interpretation": "ok"}},
        "efficiency": {"asset_turnover": {"value": 0.0,
                       "interpretation": "Insufficient data to calculate"}},
    }}
    kept = filter_ratios(raw)
    assert kept["gross_margin"] == 0.6 and kept["current_ratio"] == 2.0
    assert "debt_to_equity" not in kept   # leverage category dropped
    assert "pe_ratio" not in kept         # valuation category dropped
    assert "asset_turnover" not in kept   # insufficient-data ratio dropped
