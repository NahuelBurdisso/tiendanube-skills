"""Label-anchored reader for the 'Más Orden Más Ganancia' accounting workbook.
Reads the already-computed statements; never recomputes from raw transactions.
Multi-year aware: templates may have 24 month columns (2 years). We select the
latest year that has data and analyze that 12-month window."""
import openpyxl
from labels import normalize, col_a_index, find_month_header, read_year_row

def _num(v):
    if v is None or v == "":
        return 0
    if isinstance(v, str):
        return 0   # Excel error codes (#REF!, #DIV/0!, …) or stray text -> 0
    return float(v)

def _is_err(v):
    return isinstance(v, str) and v.startswith("#")

def read_statement_block(path, sheet, anchor, line_labels):
    """Return {months, years, lines:{normlabel:[nums]}, raw:{normlabel:[cells]}, ...}
    for one statement block, full width (may span multiple years)."""
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
    years = read_year_row(ws, hrow, start_col, n)
    lines, raw = {}, {}
    for label in line_labels:
        key = normalize(label)
        if key in idx and idx[key] > anchor_row:
            r = idx[key]
            cells = [ws.cell(r, start_col + i).value for i in range(n)]
            raw[key] = cells
            lines[key] = [_num(x) for x in cells]
    return {"months": months, "years": years, "lines": lines, "raw": raw,
            "anchorRow": anchor_row, "startCol": start_col}

def _target_year(years, ventas_full):
    """Latest year that has nonzero ventas; fallback latest labeled; None if unlabeled."""
    labeled = [y for y in (years or []) if y]
    if not labeled:
        return None
    sums = {}
    for i, y in enumerate(years):
        if y:
            val = ventas_full[i] if i < len(ventas_full) and ventas_full[i] else 0
            sums[y] = sums.get(y, 0.0) + val
    active = [y for y, s in sums.items() if s]
    return max(active) if active else max(labeled)

def _offsets_for(block, target):
    """Column offsets for `target` year in a block. If the block has no labeled
    years (or none match target), fall back to its latest 12 columns (multi-col)
    or all columns — never collapse to empty."""
    n = len(block["months"])
    if target is not None and block.get("years"):
        offs = [i for i in range(n) if i < len(block["years"]) and block["years"][i] == target]
        if offs:
            return offs
    return list(range(n - 12, n)) if n > 12 else list(range(n))

def _slice(block, offsets):
    months = [block["months"][i] for i in offsets]
    lines = {k: [v[i] for i in offsets] for k, v in block["lines"].items()}
    raw = {k: [v[i] for i in offsets] for k, v in block["raw"].items()}
    return months, lines, raw

_IS = ["Ventas","Costo reposición","Comisiones","Utilidad bruta","Costos fijos",
       "Amortización créditos","Utilidad operativa","Gastos variables","Utilidad neta"]
_CF = ["Ingresos","Egresos","TOTAL"]
_BE = ["Margen bruto", "Facturación necesaria total"]

_IS_KEYS = {
    "ventas":"ventas","costo reposicion":"costoReposicion","comisiones":"comisiones",
    "utilidad bruta":"utilidadBruta","costos fijos":"costosFijos",
    "amortizacion creditos":"amortizacion","utilidad operativa":"utilidadOperativa",
    "gastos variables":"gastosVariables","utilidad neta":"utilidadNeta"}

def parse_workbook(path, sheet="Resultados"):
    isb = read_statement_block(path, sheet, "ESTADO DE RESULTADOS", _IS)
    cfb = read_statement_block(path, sheet, "FLUJOS DE DINERO", _CF)
    try:
        beb = read_statement_block(path, sheet, "PUNTO DE EQUILIBRIO", _BE)
    except ValueError:
        beb = None

    target = _target_year(isb["years"], isb["lines"].get("ventas", []))

    is_months, is_lines, is_raw = _slice(isb, _offsets_for(isb, target))
    _, cf_lines, _ = _slice(cfb, _offsets_for(cfb, target))
    if beb:
        _, be_lines, _ = _slice(beb, _offsets_for(beb, target))
        be_margin = be_lines.get("margen bruto", [])
        be_facturacion = be_lines.get("facturacion necesaria total", [])
    else:
        be_margin = []
        be_facturacion = []

    n = len(is_months)
    is_monthly = {cam: is_lines.get(norm, [0]*n) for norm, cam in _IS_KEYS.items()}

    # warnings: error cells within the SELECTED columns of the income statement only
    warnings = []
    for key, cells in is_raw.items():
        if any(_is_err(x) for x in cells):
            warnings.append(
                f"'{key}' tiene celdas con error (#REF!/#DIV0) en Estado de Resultados "
                f"del workbook — se computan como 0; el total puede estar subestimado; "
                f"revisar la fórmula del cliente.")

    return {
        "months": is_months,
        "year": target,
        "incomeStatement": {"monthly": is_monthly},
        "cashFlow": {"monthly": {
            "ingresos": cf_lines.get("ingresos", [0]*n),
            "egresos":  cf_lines.get("egresos", [0]*n),
            "total":    cf_lines.get("total", [0]*n)}},
        "breakEven": {"margenBrutoMonthly": be_margin,
                      "facturacionEquilibrioMonthly": be_facturacion},
        "warnings": warnings,
    }
