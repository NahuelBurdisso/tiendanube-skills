import openpyxl
from workbook import parse_workbook
from financials import build_financials
from xlsx_report import write_xlsx

def test_write_xlsx_has_statements_tab(fixture_workbook, tmp_path):
    fin = build_financials(parse_workbook(fixture_workbook))
    results = {"forecast": {}, "ratios": {"gross_margin": 0.5}, "variance": {}}
    out = tmp_path / "store-finance.xlsx"
    write_xlsx(fin, results, str(out))
    wb = openpyxl.load_workbook(out)
    assert "Estado de Resultados" in wb.sheetnames
    ws = wb["Estado de Resultados"]
    # ventas row present with its annual total in the last column
    rows = list(ws.iter_rows(values_only=True))
    ventas = next(r for r in rows if r and r[0] == "Ventas")
    assert ventas[-1] == 12000   # annual total column
