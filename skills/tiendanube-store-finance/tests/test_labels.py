from labels import normalize, MONTHS, col_a_index, find_month_header
import openpyxl

def test_normalize_strips_accents_and_case():
    assert normalize("Amortización créditos") == "amortizacion creditos"
    assert normalize("  Utilidad   Neta ") == "utilidad neta"

def test_months_constant_has_12():
    assert len(MONTHS) == 12 and MONTHS[0] == "Enero"

def test_col_a_index_and_month_header(fixture_workbook):
    wb = openpyxl.load_workbook(fixture_workbook, data_only=True)
    ws = wb["Resultados"]
    idx = col_a_index(ws)
    assert idx[normalize("ESTADO DE RESULTADOS")] == 9
    assert idx[normalize("Ventas")] == 12
    row, start_col, months = find_month_header(ws, after_row=9)
    assert row == 11 and start_col == 2 and months[0] == "Enero" and len(months) == 12
