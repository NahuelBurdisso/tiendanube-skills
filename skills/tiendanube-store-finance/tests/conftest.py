import sys, pathlib
import openpyxl
import pytest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
          "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

def _write_block(ws, anchor_row, anchor_text, header_row, rows):
    ws.cell(anchor_row, 1, anchor_text)
    for i, m in enumerate(MONTHS):
        ws.cell(header_row, 2 + i, m)
    for r, (label, vals) in rows.items():
        ws.cell(r, 1, label)
        for i, v in enumerate(vals):
            ws.cell(r, 2 + i, v)

@pytest.fixture
def fixture_workbook(tmp_path):
    """Mimics the 'Más Orden Más Ganancia' Resultados sheet layout."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resultados"
    _write_block(ws, 1, "FLUJOS DE DINERO", 3, {
        4: ("Ingresos", [100]*12),
        5: ("Egresos",  [60]*12),
        6: ("TOTAL",    [40]*12),
    })
    _write_block(ws, 9, "ESTADO DE RESULTADOS", 11, {
        12: ("Ventas",               [1000]*12),
        13: ("Costo reposición",     [400]*12),
        14: ("Comisiones",           [0]*12),
        15: ("Utilidad bruta",       [600]*12),
        16: ("Costos fijos",         [100]*12),
        17: ("Amortización créditos",[None]*12),
        18: ("Utilidad operativa",   [500]*12),
        19: ("Gastos variables",     [None]*12),
        20: ("Utilidad neta",        [500]*12),
    })
    _write_block(ws, 26, "PUNTO DE EQUILIBRIO", 28, {
        29: ("Margen bruto", [0.6]*12),
    })
    st = wb.create_sheet("Stock"); st.cell(1,1,"Producto"); st.cell(1,2,"Valor"); st.cell(2,1,"Remera"); st.cell(2,2,5000)
    p = tmp_path / "client.xlsx"
    wb.save(p)
    return str(p)

@pytest.fixture
def sample_parsed(fixture_workbook):
    from workbook import parse_workbook
    return parse_workbook(fixture_workbook)

@pytest.fixture
def sample_financials_v2(sample_parsed):
    from financials import build_financials
    return build_financials(sample_parsed)
