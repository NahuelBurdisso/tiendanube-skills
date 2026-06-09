from workbook import parse_workbook
from financials import build_financials, SCHEMA_VERSION

def test_build_financials_rolls_up_annual_and_margins(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook), currency="ARS")
    assert fin["schemaVersion"] == SCHEMA_VERSION
    a = fin["incomeStatement"]["annual"]
    assert a["ventas"] == 12000          # 1000 * 12
    assert a["costoReposicion"] == 4800  # 400 * 12
    assert round(a["margenBruto"], 3) == 0.6   # 7200/12000 annual (utilidadBruta=600*12)
    assert fin["source"] == "workbook"
    assert fin["warnings"] == []   # clean fixture has no error cells

def test_active_months_full_year(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    assert fin["activeMonths"] == 12
    assert round(fin["annualizedVentas"]) == 12000

def test_active_months_trailing_zeros():
    parsed = {"months": ["Enero","Febrero","Marzo"],
        "incomeStatement": {"monthly": {
            "ventas": [100,200,0], "costoReposicion": [0,0,0], "comisiones": [0,0,0],
            "utilidadBruta": [50,100,0], "costosFijos": [0,0,0], "amortizacion": [0,0,0],
            "utilidadOperativa": [0,0,0], "gastosVariables": [0,0,0], "utilidadNeta": [10,20,0]}},
        "cashFlow": {"monthly": {"ingresos":[0,0,0],"egresos":[0,0,0],"total": [0,0,0]}},
        "breakEven": {"margenBrutoMonthly": []}, "warnings": [], "year": 2026}
    fin = build_financials(parsed)
    assert fin["activeMonths"] == 2
    assert round(fin["annualizedVentas"]) == 1800   # 300 / 2 * 12
