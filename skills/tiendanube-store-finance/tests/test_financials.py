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
