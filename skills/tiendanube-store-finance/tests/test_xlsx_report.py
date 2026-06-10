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

def test_write_xlsx_includes_warnings_sheet(fixture_workbook, tmp_path):
    import openpyxl
    from workbook import parse_workbook
    from financials import build_financials
    from xlsx_report import write_xlsx
    fin = build_financials(parse_workbook(fixture_workbook))
    fin["warnings"] = ["'utilidad neta' tiene celdas con error (#REF!) en el workbook"]
    out = tmp_path / "w.xlsx"
    write_xlsx(fin, {"forecast": {}, "ratios": {}, "variance": {}}, str(out))
    wb = openpyxl.load_workbook(out)
    assert "Advertencias" in wb.sheetnames
    rows = [r[0] for r in wb["Advertencias"].iter_rows(values_only=True)]
    assert any("#REF!" in (r or "") for r in rows)


def test_xlsx_has_new_tabs(fixture_workbook, tmp_path):
    from fiscal import apply_fiscal
    from restatement import restate
    from levers import build_levers
    cfg = {"fiscal": {"regimen": "monotributo", "categoriaMonotributo": "A"}, "finance": {}}
    fin = build_financials(parse_workbook(fixture_workbook))
    fin = apply_fiscal(fin, cfg)
    fin = restate(fin, cfg["finance"])
    results = {"forecast": {}, "variance": {}, "ratios": {}, "levers": build_levers(fin, cfg)}
    out = tmp_path / "f.xlsx"
    write_xlsx(fin, results, str(out))
    wb = openpyxl.load_workbook(out)
    for tab in ["Estado de Resultados", "Reexpresión", "Posición fiscal",
                "Variación", "Ratios", "Palancas", "Proyección", "Supuestos"]:
        assert tab in wb.sheetnames, f"missing tab: {tab}"
