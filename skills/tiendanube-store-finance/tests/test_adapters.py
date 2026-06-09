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

def test_ratios_cogs_reconciles_to_statement_gross_margin():
    from adapters import to_ratios_input
    fin = {
        "incomeStatement": {"annual": {
            "ventas": 1000.0, "costoReposicion": 400.0, "comisiones": 100.0,
            "utilidadBruta": 500.0, "utilidadOperativa": 300.0,
            "utilidadNeta": 200.0, "amortizacion": 0.0}},
        "balanceSheetPartial": {"inventory": 0, "accountsReceivable": 0, "accountsPayable": 0},
        "cashFlow": {"monthly": {"total": [0]}},
    }
    inp = to_ratios_input(fin)
    cogs = inp["income_statement"]["cost_of_goods_sold"]
    assert cogs == 500.0  # ventas - utilidadBruta, NOT costoReposicion (400)
    # ratio gross margin = (revenue - cogs)/revenue == statement margenBruto (500/1000)
    gm = (inp["income_statement"]["revenue"] - cogs) / inp["income_statement"]["revenue"]
    assert abs(gm - 0.5) < 1e-9


def test_variance_input_period_over_period(fixture_workbook):
    inp = to_variance_input(_fin(fixture_workbook))
    names = {li["name"] for li in inp["line_items"]}
    assert "Ventas" in names
    v = next(li for li in inp["line_items"] if li["name"] == "Ventas")
    assert v["actual"] == 1000 and v["prior_year"] == 1000  # flat fixture
    assert "budget" not in v or v["budget"] == 0  # no budget exists

def test_variance_uses_active_window():
    from adapters import to_variance_input
    fin = {"incomeStatement": {"monthly": {"ventas": [100,200,0,0]}},
           "months": ["E","F","M","A"], "activeMonths": 2, "storeName": None}
    inp = to_variance_input(fin)
    v = next(li for li in inp["line_items"] if li["name"] == "Ventas")
    assert v["actual"] == 200 and v["prior_year"] == 100   # last active vs prior, NOT trailing zeros

def test_forecast_trims_trailing_zeros():
    from financials import build_financials
    from adapters import to_forecast_input
    parsed = {"months": ["E","F","M","A"],
        "incomeStatement": {"monthly": {
            "ventas": [100,200,0,0], "costoReposicion": [0,0,0,0], "comisiones": [0,0,0,0],
            "utilidadBruta": [100,200,0,0], "costosFijos": [0,0,0,0], "amortizacion": [0,0,0,0],
            "utilidadOperativa": [0,0,0,0], "gastosVariables": [0,0,0,0], "utilidadNeta": [0,0,0,0]}},
        "cashFlow": {"monthly": {"ingresos":[0,0,0,0],"egresos":[0,0,0,0],"total": [0,0,0,0]}},
        "breakEven": {"margenBrutoMonthly": []}, "warnings": [], "year": 2026}
    fin = build_financials(parsed)
    inp = to_forecast_input(fin, {})
    assert len(inp["historical_periods"]) == 2          # trailing zeros trimmed
    assert inp["historical_periods"][-1]["revenue"] == 200
