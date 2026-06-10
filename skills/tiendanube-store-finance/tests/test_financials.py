from workbook import parse_workbook
from financials import build_financials, SCHEMA_VERSION
from measures import nom

def test_build_financials_rolls_up_annual_and_margins(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook), currency="ARS")
    assert fin["schemaVersion"] == SCHEMA_VERSION
    a = fin["incomeStatement"]["annual"]
    assert nom(a["ventas"]) == 12000          # 1000 * 12
    assert nom(a["costoReposicion"]) == 4800  # 400 * 12
    assert round(a["margenBruto"], 3) == 0.6   # 7200/12000 annual (utilidadBruta=600*12)
    assert fin["source"] == "workbook"
    assert fin["warnings"] == []   # clean fixture has no error cells

def test_active_months_full_year(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    assert fin["activeMonths"] == 12
    assert round(fin["annualizedVentas"]) == 12000

def test_monthly_lines_are_measures(sample_parsed):
    from financials import build_financials
    fin = build_financials(sample_parsed)
    assert fin["schemaVersion"] == "2.0"
    ventas0 = fin["incomeStatement"]["monthly"]["ventas"][0]
    assert set(ventas0) == {"nominal", "real", "source", "transforms"}
    assert ventas0["source"] == "fact" and ventas0["real"] is None

def test_annual_lines_are_measures_and_tie_out(sample_parsed):
    from financials import build_financials
    from measures import nom
    fin = build_financials(sample_parsed)
    monthly = fin["incomeStatement"]["monthly"]["ventas"]
    annual = fin["incomeStatement"]["annual"]["ventas"]
    assert abs(nom(annual) - sum(nom(x) for x in monthly)) < 1e-6

def test_margins_stay_scalar(sample_parsed):
    from financials import build_financials
    fin = build_financials(sample_parsed)
    assert isinstance(fin["incomeStatement"]["annual"]["margenBruto"], float)

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


def _parsed_with_be(facturacion):
    keys = ["ventas","costoReposicion","comisiones","utilidadBruta","costosFijos",
            "amortizacion","utilidadOperativa","gastosVariables","utilidadNeta"]
    n = len(facturacion) if facturacion else 2
    mp = {k: [0]*n for k in keys}; mp["ventas"] = [1000]*n
    return {"months": ["Enero","Febrero"][:n], "year": 2025,
            "incomeStatement": {"monthly": mp},
            "cashFlow": {"monthly": {"ingresos":[0]*n,"egresos":[0]*n,"total":[0]*n}},
            "breakEven": {"margenBrutoMonthly": [], "facturacionEquilibrioMonthly": facturacion},
            "warnings": []}

def test_break_even_safety_margin_computed():
    from financials import build_financials
    fin = build_financials(_parsed_with_be([950, 950]))   # ventas 2000, FE 1900
    assert abs(fin["breakEven"]["margenSeguridad"] - 0.05) < 1e-9
    assert fin["breakEven"]["facturacionParaColchon"] > 0   # FE/0.8 - 2000 = 375

def test_break_even_safety_none_when_no_facturacion():
    from financials import build_financials
    fin = build_financials(_parsed_with_be([]))            # workbook didn't fill it
    assert fin["breakEven"]["margenSeguridad"] is None      # never a fake 100% cushion
