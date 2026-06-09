from workbook import parse_workbook
from financials import build_financials
from adapters import to_forecast_input, to_ratios_input, to_variance_input

def _fin(fixture_workbook):
    return build_financials(parse_workbook(fixture_workbook))

def test_forecast_input_shape(fixture_workbook):
    cfg = {"forecastPeriods": 12, "scenarios": {
        "base": {"growth_adjustment": 0, "margin_adjustment": 0}}}
    inp = to_forecast_input(_fin(fixture_workbook), cfg)
    assert len(inp["historical_periods"]) == 12
    assert inp["historical_periods"][0]["revenue"] == 1000
    assert round(inp["assumptions"]["gross_margin"], 3) == 0.6
    assert "base" in inp["scenarios"] and inp["forecast_periods"] == 12

def test_ratios_input_maps_statement(fixture_workbook):
    inp = to_ratios_input(_fin(fixture_workbook))
    assert inp["income_statement"]["revenue"] == 12000
    assert inp["income_statement"]["cost_of_goods_sold"] == 4800
    assert inp["income_statement"]["operating_income"] == 6000  # 500*12
    assert inp["balance_sheet"].get("total_debt", 0) == 0

def test_variance_input_period_over_period(fixture_workbook):
    inp = to_variance_input(_fin(fixture_workbook))
    names = {li["name"] for li in inp["line_items"]}
    assert "Ventas" in names
    v = next(li for li in inp["line_items"] if li["name"] == "Ventas")
    assert v["actual"] == 1000 and v["prior_year"] == 1000  # flat fixture
    assert "budget" not in v or v["budget"] == 0  # no budget exists
