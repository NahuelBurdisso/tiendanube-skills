"""Label-anchored reader for the 'Más Orden Más Ganancia' accounting workbook.
Reads the already-computed statements; never recomputes from raw transactions."""
import openpyxl
from labels import normalize, col_a_index, find_month_header

def _num(v):
    """Convert a cell value to float; treat None, blank, or Excel errors as 0."""
    if v is None or v == "":
        return 0
    if isinstance(v, str):
        # Excel formula errors (#REF!, #DIV/0!, etc.) → treat as 0
        return 0
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0

def read_statement_block(path, sheet, anchor, line_labels):
    """Return {months:[...], lines:{normalized_label:[12 floats]}} for one block."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    if sheet not in wb.sheetnames:
        raise ValueError(f"sheet {sheet!r} not in {wb.sheetnames}")
    ws = wb[sheet]
    idx = col_a_index(ws)
    a = normalize(anchor)
    if a not in idx:
        raise ValueError(f"anchor {anchor!r} not found in {sheet}")
    anchor_row = idx[a]
    hrow, start_col, months = find_month_header(ws, after_row=anchor_row)
    n = len(months)
    lines = {}
    for label in line_labels:
        key = normalize(label)
        if key in idx and idx[key] > anchor_row:
            r = idx[key]
            lines[key] = [_num(ws.cell(r, start_col + i).value) for i in range(n)]
    return {"months": months, "lines": lines, "anchorRow": anchor_row, "startCol": start_col}

# canonical line label sets
_IS = ["Ventas","Costo reposición","Comisiones","Utilidad bruta","Costos fijos",
       "Amortización créditos","Utilidad operativa","Gastos variables","Utilidad neta"]
_CF = ["Ingresos","Egresos","TOTAL"]
_BE = ["Margen bruto"]

_IS_KEYS = {  # normalized label -> canonical camelCase
    "ventas":"ventas","costo reposicion":"costoReposicion","comisiones":"comisiones",
    "utilidad bruta":"utilidadBruta","costos fijos":"costosFijos",
    "amortizacion creditos":"amortizacion","utilidad operativa":"utilidadOperativa",
    "gastos variables":"gastosVariables","utilidad neta":"utilidadNeta"}

def parse_workbook(path, sheet="Resultados"):
    isb = read_statement_block(path, sheet, "ESTADO DE RESULTADOS", _IS)
    cfb = read_statement_block(path, sheet, "FLUJOS DE DINERO", _CF)
    try:
        beb = read_statement_block(path, sheet, "PUNTO DE EQUILIBRIO", _BE)
        be_margin = beb["lines"].get("margen bruto", [])
    except ValueError:
        be_margin = []
    n = len(isb["months"])
    is_monthly = {cam: isb["lines"].get(norm, [0]*n) for norm, cam in _IS_KEYS.items()}
    return {
        "months": isb["months"],
        "incomeStatement": {"monthly": is_monthly},
        "cashFlow": {"monthly": {
            "ingresos": cfb["lines"].get("ingresos", [0]*n),
            "egresos":  cfb["lines"].get("egresos", [0]*n),
            "total":    cfb["lines"].get("total", [0]*n)}},
        "breakEven": {"margenBrutoMonthly": be_margin},
    }
