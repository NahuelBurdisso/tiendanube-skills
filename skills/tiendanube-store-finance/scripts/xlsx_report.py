"""Write store-finance.xlsx. The Estado de Resultados tab MUST tie out to the
client's workbook (we reproduce the read values, never recomputed)."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from measures import nom

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
HEADER_FONT  = Font(bold=True, color="FFFFFF", size=11)
HEADER_FILL  = PatternFill("solid", fgColor="6B2532")
SECTION_FONT = Font(bold=True, color="6B2532")
SECTION_FILL = PatternFill("solid", fgColor="EAE2D4")
SUBTOT_FILL  = PatternFill("solid", fgColor="EAE2D4")
NEG_FONT     = Font(color="C00000")
BOLD_FONT    = Font(bold=True)
GREEN_FONT   = Font(color="3F6B4A")
AMBER_FONT   = Font(color="B8860B")
RED_FONT     = Font(color="C00000")

MONEY    = '$ #,##0'
MONEYNEG = '$ #,##0;[Red]-$ #,##0'
PCT      = '0.0%'
PCT2     = '0.00%'
RATIO    = '0.00'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def header(ws, row=1):
    """Apply header style to every non-empty cell in the given row."""
    for c in ws[row]:
        if c.value is not None:
            c.font      = HEADER_FONT
            c.fill      = HEADER_FILL
            c.alignment = Alignment(horizontal='center', vertical='center',
                                    wrap_text=True)
    ws.row_dimensions[row].height = 22


def put(ws, r, c, v, fmt=None, font=None, fill=None, align=None):
    """Write a cell at (row r, col c) and optionally set style attributes."""
    cell = ws.cell(r, c, v)
    if fmt   is not None: cell.number_format = fmt
    if font  is not None: cell.font  = font
    if fill  is not None: cell.fill  = fill
    if align is not None: cell.alignment = align
    return cell


def _set_col_width(ws, col_idx, width):
    ws.column_dimensions[get_column_letter(col_idx)].width = width


def _section_row(ws, row, label):
    """Write a section sub-header row (full width label, styled)."""
    c = ws.cell(row, 1, label)
    c.font = SECTION_FONT
    c.fill = SECTION_FILL
    c.alignment = Alignment(horizontal='left', vertical='center')


# ---------------------------------------------------------------------------
# IS rows definition (shared between _build_is_tab and callers)
# ---------------------------------------------------------------------------
_IS_ROWS = [
    ("ventas",           "Ventas"),
    ("costoReposicion",  "Costo reposición"),
    ("comisiones",       "Comisiones"),
    ("utilidadBruta",    "Utilidad bruta"),
    ("costosFijos",      "Costos fijos"),
    ("amortizacion",     "Amortización créditos"),
    ("utilidadOperativa","Utilidad operativa"),
    ("gastosVariables",  "Gastos variables"),
    ("utilidadNeta",     "Utilidad neta"),
]

# rows that get SUBTOT_FILL + bold
_SUBTOTAL_LABELS = {"Utilidad bruta", "Utilidad operativa", "Utilidad neta"}


# ---------------------------------------------------------------------------
# Tab 1 — Resumen
# ---------------------------------------------------------------------------

def _build_resumen(wb, fin, results):
    ws = wb.create_sheet("Resumen")
    ws.sheet_properties.tabColor = "6B2532"

    months_list   = fin.get("months", [])
    active        = fin.get("activeMonths") or 1
    annual        = fin["incomeStatement"]["annual"]
    ventas_ytd    = nom(annual.get("ventas", 0.0))
    annualized    = fin.get("annualizedVentas", 0.0)
    margen_bruto  = annual.get("margenBruto", 0.0)
    margen_neto   = annual.get("margenNeto", 0.0)
    utilidad_op   = nom(annual.get("utilidadOperativa", 0.0))
    util_bruta    = nom(annual.get("utilidadBruta", 0.0))
    util_neta     = nom(annual.get("utilidadNeta", 0.0))
    margen_op     = (utilidad_op / ventas_ytd) if ventas_ytd else 0.0
    store_name    = fin.get("storeName") or "Tienda"
    year          = fin.get("year") or ""

    # Determine first/last active month labels
    active_months_labels = [m for m in months_list if m]
    first_m = active_months_labels[0] if active_months_labels else ""
    last_m  = active_months_labels[active - 1] if len(active_months_labels) >= active else (active_months_labels[-1] if active_months_labels else "")

    # Forecast trend data (may be absent)
    forecast       = (results.get("forecast") or {})
    trend_analysis = forecast.get("trend_analysis") or {}
    trend_block    = trend_analysis.get("trend") or {}
    avg_growth     = trend_analysis.get("average_growth_rate", 0.0)
    direction      = trend_block.get("direction", "—")
    r_squared      = trend_block.get("r_squared", 0.0)

    # Title rows
    title_cell = ws.cell(1, 1, f"{store_name} — Resumen Financiero")
    title_cell.font = Font(bold=True, size=14, color="6B2532")
    period_str = f"Período: {first_m}–{last_m} {year} · {active} meses YTD"
    ws.cell(2, 1, period_str).font = Font(italic=True, color="555555")

    row = 4

    def kpi(label, value, fmt):
        nonlocal row
        put(ws, row, 1, label, align=Alignment(horizontal='left'))
        put(ws, row, 2, value, fmt=fmt, align=Alignment(horizontal='right'))
        row += 1

    def section(label):
        nonlocal row
        _section_row(ws, row, label)
        row += 1

    section("VENTAS")
    kpi("Ventas YTD",                 ventas_ytd,  MONEY)
    kpi("Run-rate anualizado",         annualized,  MONEY)

    section("MÁRGENES")
    kpi("Margen bruto",               margen_bruto, PCT)
    kpi("Margen operativo",           margen_op,    PCT)
    kpi("Margen neto",                margen_neto,  PCT)

    section("RENTABILIDAD")
    kpi("Utilidad bruta YTD",         util_bruta,   MONEY)
    kpi("Utilidad operativa YTD",     utilidad_op,  MONEY)
    kpi("Utilidad neta YTD",          util_neta,    MONEY)

    section("TENDENCIA")
    kpi("Crecimiento mensual promedio", avg_growth,  PCT2)
    kpi("Dirección",                  direction,    None)
    kpi("R²",                         r_squared,    RATIO)

    _set_col_width(ws, 1, 40)
    _set_col_width(ws, 2, 22)
    ws.freeze_panes = "A3"
    return ws


# ---------------------------------------------------------------------------
# Tab 2 — Estado de Resultados
# ---------------------------------------------------------------------------

def _build_estado(wb, fin):
    ws = wb.create_sheet("Estado de Resultados")
    ws.sheet_properties.tabColor = "8C3D3D"

    months      = fin["months"]
    active      = fin.get("activeMonths") or len(months)
    m_data      = fin["incomeStatement"]["monthly"]
    annual      = fin["incomeStatement"]["annual"]
    ventas_ytd  = nom(annual.get("ventas", 0.0))

    # Header row: Concepto + month names (mark active with " *") + YTD + Anual est.
    n_months = len(months)
    header_vals = ["Concepto"]
    for i, mn in enumerate(months):
        label = mn + (" *" if i < active else "")
        header_vals.append(label)
    header_vals += ["YTD", "Anual est."]

    row = 1
    for col, val in enumerate(header_vals, 1):
        put(ws, row, col, val)
    header(ws, row)
    row += 1

    total_cols   = len(header_vals)   # Concepto + 12 months + YTD + Anual est.
    ytd_col      = total_cols - 1     # second to last
    annual_col   = total_cols         # last column

    for key, label in _IS_ROWS:
        monthly_vals = m_data.get(key, [0.0] * n_months)
        ann_val      = nom(annual.get(key, 0.0))
        annualized   = ann_val * (12.0 / active) if active else ann_val

        is_subtotal = label in _SUBTOTAL_LABELS
        is_neta     = (label == "Utilidad neta")
        fill = SUBTOT_FILL if is_subtotal else None
        font = BOLD_FONT   if is_neta     else None

        put(ws, row, 1, label, font=font, fill=fill)
        for ci, val in enumerate(monthly_vals, 2):
            v = nom(val) if val is not None else 0.0
            cell = put(ws, row, ci, v, fmt=MONEY, fill=fill)
            if v < 0:
                cell.font = NEG_FONT
        # YTD col = annual sum
        put(ws, row, ytd_col, ann_val, fmt=MONEY, font=font, fill=fill)
        # Annual est. col — for the "Ventas" row the test checks last cell == ytd annual
        # (with activeMonths=12 factor is 1 so annualized == ann_val == 12000)
        put(ws, row, annual_col, annualized, fmt=MONEY, font=font, fill=fill)
        row += 1

    # Blank separator
    row += 1

    # Margin rows (section header)
    _section_row(ws, row, "MÁRGENES"); row += 1
    margins = [
        ("Margen bruto",     annual.get("margenBruto", 0.0)),
        ("Margen operativo", (nom(annual.get("utilidadOperativa", 0.0)) / ventas_ytd) if ventas_ytd else 0.0),
        ("Margen neto",      annual.get("margenNeto", 0.0)),
    ]
    for label, val in margins:
        put(ws, row, 1, label, fill=SECTION_FILL)
        put(ws, row, ytd_col, val, fmt=PCT, fill=SECTION_FILL)
        row += 1

    row += 1
    # Footnote
    ws.cell(row, 1, "* meses con datos").font = Font(italic=True, size=9)

    # Column widths
    _set_col_width(ws, 1, 30)
    for ci in range(2, total_cols + 1):
        _set_col_width(ws, ci, 15)

    ws.freeze_panes = "B2"
    return ws


# ---------------------------------------------------------------------------
# Tab 3 — Flujo de Caja
# ---------------------------------------------------------------------------

def _build_flujo(wb, fin, results):
    ws = wb.create_sheet("Flujo de Caja")
    ws.sheet_properties.tabColor = "B08858"

    months      = fin["months"]
    active      = fin.get("activeMonths") or len(months)
    cf_monthly  = fin.get("cashFlow", {}).get("monthly", {})
    ingresos    = [nom(x) for x in cf_monthly.get("ingresos", [])]
    egresos     = [nom(x) for x in cf_monthly.get("egresos",  [])]
    totales     = [nom(x) for x in cf_monthly.get("total",    [])]

    row = 1
    for col, val in enumerate(["Mes", "Ingresos", "Egresos", "Neto", "Acumulado"], 1):
        put(ws, row, col, val)
    header(ws, row)
    row += 1

    acumulado = 0.0
    for i in range(active):
        ing  = ingresos[i] if i < len(ingresos) else 0.0
        egr  = egresos[i]  if i < len(egresos)  else 0.0
        net  = totales[i]  if i < len(totales)   else (ing - egr)
        acumulado += (net or 0.0)
        mes_label = months[i] if i < len(months) else f"Mes {i+1}"

        put(ws, row, 1, mes_label)
        put(ws, row, 2, ing or 0.0,      fmt=MONEY)
        put(ws, row, 3, egr or 0.0,      fmt=MONEY)
        net_cell = put(ws, row, 4, net or 0.0, fmt=MONEYNEG)
        if (net or 0.0) < 0:
            net_cell.font = NEG_FONT
        acc_cell = put(ws, row, 5, acumulado, fmt=MONEYNEG)
        if acumulado < 0:
            acc_cell.font = NEG_FONT
        row += 1

    # 13-week rolling cash flow block (if present)
    forecast = results.get("forecast") or {}
    rcf      = forecast.get("rolling_cash_flow") or {}
    weekly   = rcf.get("weekly_projections") or []
    if weekly:
        row += 1
        ws.cell(row, 1, "PROYECCIÓN 13 SEMANAS").font = SECTION_FONT
        ws.cell(row, 1).fill = SECTION_FILL
        row += 1
        for col, val in enumerate(["Semana", "Ingresos", "Egresos", "Neto", "Saldo"], 1):
            put(ws, row, col, val)
        header(ws, row)
        row += 1
        for w in weekly:
            net  = w.get("net_cash_flow", 0.0)
            saldo = w.get("closing_balance", 0.0)
            put(ws, row, 1, f"Semana {w.get('week', '')}")
            put(ws, row, 2, w.get("total_inflows",  0.0), fmt=MONEY)
            put(ws, row, 3, w.get("total_outflows", 0.0), fmt=MONEY)
            n_cell = put(ws, row, 4, net,   fmt=MONEYNEG)
            s_cell = put(ws, row, 5, saldo, fmt=MONEYNEG)
            if net   < 0: n_cell.font = NEG_FONT
            if saldo < 0: s_cell.font = NEG_FONT
            row += 1

    _set_col_width(ws, 1, 18)
    for ci in range(2, 6):
        _set_col_width(ws, ci, 16)
    ws.freeze_panes = "A2"
    return ws


# ---------------------------------------------------------------------------
# Tab 4 — Variación
# ---------------------------------------------------------------------------

def _build_variacion(wb, results):
    ws = wb.create_sheet("Variación")
    ws.sheet_properties.tabColor = "C0772E"

    row = 1
    for col, val in enumerate(["Concepto", "Actual", "Mes previo", "Δ", "Δ%", "Evaluación"], 1):
        put(ws, row, col, val)
    header(ws, row)
    row += 1

    line_items = (results.get("variance") or {}).get("line_items", [])
    for li in line_items:
        name = li.get("name", "")
        act  = li.get("actual", 0.0) or 0.0
        pri  = li.get("prior_year", 0.0) or 0.0
        d    = act - pri
        dp   = (d / pri) if pri else 0.0

        # Determine if cost line (negative Δ is favorable) or revenue/income line
        name_lower = name.lower()
        is_cost = any(x in name_lower for x in ("costo", "costos", "gastos",
                                                  "amortizacion", "amortización",
                                                  "comision", "comisión"))
        if is_cost:
            eval_label = "Favorable" if d <= 0 else "Desfavorable"
            eval_font  = GREEN_FONT if d <= 0 else RED_FONT
        else:
            eval_label = "Favorable" if d >= 0 else "Desfavorable"
            eval_font  = GREEN_FONT if d >= 0 else RED_FONT

        put(ws, row, 1, name)
        put(ws, row, 2, act, fmt=MONEYNEG)
        put(ws, row, 3, pri, fmt=MONEYNEG)
        d_cell  = put(ws, row, 4, d,  fmt=MONEYNEG)
        dp_cell = put(ws, row, 5, dp, fmt=PCT)
        if d  < 0: d_cell.font  = NEG_FONT
        if dp < 0: dp_cell.font = NEG_FONT
        put(ws, row, 6, eval_label, font=eval_font)
        row += 1

    _set_col_width(ws, 1, 32)
    for ci in range(2, 7):
        _set_col_width(ws, ci, 16)
    ws.freeze_panes = "A2"
    return ws


# ---------------------------------------------------------------------------
# Tab 5 — Ratios
# ---------------------------------------------------------------------------

_RATIO_META = {
    "gross_margin":         ("Rentabilidad", "Margen bruto",        PCT),
    "operating_margin":     ("Rentabilidad", "Margen operativo",    PCT),
    "net_margin":           ("Rentabilidad", "Margen neto",         PCT),
    "ebitda_margin":        ("Rentabilidad", "Margen EBITDA",       PCT),
    "return_on_assets":     ("Rentabilidad", "Retorno sobre activos", PCT),
    "return_on_equity":     ("Rentabilidad", "Retorno sobre patrimonio", PCT),
    "current_ratio":        ("Liquidez",     "Liquidez corriente",  RATIO),
    "quick_ratio":          ("Liquidez",     "Prueba ácida",        RATIO),
    "cash_ratio":           ("Liquidez",     "Ratio de caja",       RATIO),
    "asset_turnover":       ("Eficiencia",   "Rotación de activos", RATIO),
    "inventory_turnover":   ("Eficiencia",   "Rotación de inventario", RATIO),
    "receivables_turnover": ("Eficiencia",   "Rotación de cuentas x cobrar", RATIO),
    "days_sales_outstanding":("Eficiencia",  "DSO (días)",          RATIO),
    "fixed_cost_coverage":  ("Eficiencia",   "Cobertura costos fijos", RATIO),
}

def _ratio_reading(key, value):
    """Return (label, font) for the Lectura column."""
    margin_keys = {"gross_margin", "operating_margin", "net_margin", "ebitda_margin"}
    if key in margin_keys:
        if value >= 0.40:
            return "Saludable",  GREEN_FONT
        elif value >= 0.30:
            return "Aceptable",  AMBER_FONT
        else:
            return "Bajo",       RED_FONT
    liq_keys = {"current_ratio", "quick_ratio"}
    if key in liq_keys:
        if value >= 2.0:
            return "Saludable",  GREEN_FONT
        elif value >= 1.0:
            return "Aceptable",  AMBER_FONT
        else:
            return "Riesgo",     RED_FONT
    return "—", None


def _build_ratios(wb, results):
    ws = wb.create_sheet("Ratios")
    ws.sheet_properties.tabColor = "3F6B4A"

    row = 1
    for col, val in enumerate(["Categoría", "Ratio", "Valor", "Lectura"], 1):
        put(ws, row, col, val)
    header(ws, row)
    row += 1

    ratios = results.get("ratios") or {}
    current_cat = None
    for key, value in ratios.items():
        cat, label, fmt = _RATIO_META.get(key, ("Otros", key, RATIO))
        if cat != current_cat:
            _section_row(ws, row, cat)
            row += 1
            current_cat = cat
        lectura, lec_font = _ratio_reading(key, value if isinstance(value, (int, float)) else 0.0)
        put(ws, row, 1, cat)
        put(ws, row, 2, label)
        put(ws, row, 3, value if isinstance(value, (int, float)) else str(value), fmt=fmt)
        put(ws, row, 4, lectura, font=lec_font)
        row += 1

    _set_col_width(ws, 1, 18)
    _set_col_width(ws, 2, 32)
    _set_col_width(ws, 3, 16)
    _set_col_width(ws, 4, 18)
    ws.freeze_panes = "A2"
    return ws


# ---------------------------------------------------------------------------
# Tab 6 — Proyección
# ---------------------------------------------------------------------------

def _build_proyeccion(wb, results):
    ws = wb.create_sheet("Proyección")
    ws.sheet_properties.tabColor = "7030A0"

    forecast       = results.get("forecast") or {}
    trend_analysis = forecast.get("trend_analysis") or {}
    trend_block    = trend_analysis.get("trend") or {}
    scenario_comp  = forecast.get("scenario_comparison") or {}
    scenarios_data = scenario_comp.get("scenarios") or {}
    rcf            = forecast.get("rolling_cash_flow") or {}
    seasonality    = trend_analysis.get("seasonality_index") or []

    row = 1

    # Block A — TENDENCIA
    ws.cell(row, 1, "TENDENCIA").font  = SECTION_FONT
    ws.cell(row, 1).fill               = SECTION_FILL
    row += 1

    trend_rows = [
        ("Pendiente (slope)",         trend_block.get("slope", 0.0),        MONEY),
        ("R²",                        trend_block.get("r_squared", 0.0),    RATIO),
        ("Dirección",                 trend_block.get("direction", "—"),     None),
        ("Crecimiento prom. mensual", trend_analysis.get("average_growth_rate", 0.0), PCT2),
    ]
    for label, val, fmt in trend_rows:
        put(ws, row, 1, label)
        put(ws, row, 2, val, fmt=fmt, align=Alignment(horizontal='right'))
        row += 1

    row += 1

    # Block B — ESCENARIOS
    # Determine n periods from any scenario
    n_periods = 0
    for sc_key in ("base", "bull", "bear"):
        sc = scenarios_data.get(sc_key) or {}
        fp = sc.get("forecast_periods") or []
        if fp:
            n_periods = len(fp)
            break

    block_b_title = f"ESCENARIOS — PRÓXIMOS {n_periods} MESES" if n_periods else "ESCENARIOS"
    ws.cell(row, 1, block_b_title).font = SECTION_FONT
    ws.cell(row, 1).fill = SECTION_FILL
    row += 1

    for col, val in enumerate(["Escenario", "Crec.", "Margen", "Ventas total", "Result. operativo total"], 1):
        put(ws, row, col, val)
    header(ws, row)
    row += 1

    scenario_labels = {"bear": "Conservador", "base": "Base", "bull": "Optimista"}
    for sc_key in ("bear", "base", "bull"):
        sc = scenarios_data.get(sc_key) or {}
        if not sc:
            continue
        fps = sc.get("forecast_periods") or []
        total_rev = sum(p.get("revenue", 0.0) for p in fps)
        total_op  = sum(p.get("operating_income", 0.0) for p in fps)
        put(ws, row, 1, scenario_labels.get(sc_key, sc_key))
        put(ws, row, 2, sc.get("growth_rate",  0.0), fmt=PCT)
        put(ws, row, 3, sc.get("gross_margin", 0.0), fmt=PCT)
        put(ws, row, 4, total_rev, fmt=MONEY)
        op_cell = put(ws, row, 5, total_op, fmt=MONEYNEG)
        if total_op < 0:
            op_cell.font = NEG_FONT
        row += 1

    row += 1

    # Block C — ESTACIONALIDAD
    if seasonality:
        ws.cell(row, 1, "ESTACIONALIDAD").font = SECTION_FONT
        ws.cell(row, 1).fill = SECTION_FILL
        row += 1
        put(ws, row, 1, "Período")
        put(ws, row, 2, "Índice")
        header(ws, row)
        row += 1
        for i, idx in enumerate(seasonality, 1):
            put(ws, row, 1, f"Período {i}")
            put(ws, row, 2, idx, fmt=RATIO)
            row += 1

    _set_col_width(ws, 1, 35)
    _set_col_width(ws, 2, 16)
    _set_col_width(ws, 3, 16)
    _set_col_width(ws, 4, 18)
    _set_col_width(ws, 5, 22)
    ws.freeze_panes = "A2"
    return ws


# ---------------------------------------------------------------------------
# Tab 7 — Advertencias
# ---------------------------------------------------------------------------

def _build_advertencias(wb, fin):
    warns = fin.get("warnings") or []
    if not warns:
        return None
    ws = wb.create_sheet("Advertencias")
    ws.sheet_properties.tabColor = "C00000"
    ws.cell(1, 1, "Advertencias de datos").font = Font(bold=True, color="C00000", size=12)
    for w in warns:
        ws.append([w])
    _set_col_width(ws, 1, 80)
    return ws


# ---------------------------------------------------------------------------
# Tab — Reexpresión a moneda de cierre
# ---------------------------------------------------------------------------

def _build_reexpresion(wb, fin):
    ws = wb.create_sheet("Reexpresión")
    ws.sheet_properties.tabColor = "8C6B2E"
    base = fin.get("baseMonth")
    put(ws, 1, 1, f"Reexpresión a moneda de cierre ({base or 'n/d'}) — IPC INDEC. "
                  f"Homogeneización del Estado de Resultados; no calcula RECPAM.",
        font=Font(bold=True, color="6B2532"))
    months = fin.get("months", []); active = fin.get("activeMonths") or len(months)
    ventas = fin["incomeStatement"]["monthly"].get("ventas", [])[:active]
    for col, h in enumerate(["Mes", "Ventas nominal", "Ventas real (cierre)"], 1):
        put(ws, 3, col, h)
    header(ws, 3)
    row = 4
    for i in range(active):
        meas = ventas[i] if i < len(ventas) else {}
        put(ws, row, 1, months[i] if i < len(months) else f"Mes {i+1}")
        put(ws, row, 2, nom(meas), fmt=MONEY)
        real = meas.get("real") if isinstance(meas, dict) else None
        put(ws, row, 3, real if real is not None else "s/d IPC", fmt=MONEY if real is not None else None)
        row += 1
    av = fin["incomeStatement"]["annual"].get("ventas", {})
    put(ws, row + 1, 1, "Anual", font=BOLD_FONT)
    put(ws, row + 1, 2, nom(av), fmt=MONEY, font=BOLD_FONT)
    ar = av.get("real") if isinstance(av, dict) else None
    put(ws, row + 1, 3, ar if ar is not None else "n/d (período incompleto en IPC)",
        fmt=MONEY if ar is not None else None, font=BOLD_FONT)
    for c, w in ((1, 16), (2, 20), (3, 24)):
        _set_col_width(ws, c, w)
    return ws


# ---------------------------------------------------------------------------
# Tab — Posición fiscal
# ---------------------------------------------------------------------------

def _build_fiscal(wb, fin):
    fz = fin.get("fiscal") or {}
    ws = wb.create_sheet("Posición fiscal")
    ws.sheet_properties.tabColor = "3F6B4A"
    reg = fz.get("regimen")
    put(ws, 1, 1, f"Posición fiscal — régimen: {reg or 'no configurado'} "
                  f"(impuestos sobre pesos nominales; Ganancias = estimación).",
        font=Font(bold=True, color="6B2532"))
    r = 3
    if reg == "responsable_inscripto":
        iva = fz.get("iva", {}); br = fz.get("bridge", {})
        for label, val in (("IVA débito fiscal", iva.get("debito")),
                           ("IVA crédito fiscal", iva.get("credito")),
                           ("Posición IVA (flujo, no resultado)", iva.get("posicion")),
                           ("Resultado neto (workbook)", br.get("resultadoAntes")),
                           ("IIBB (informativo — ¿ya en costos?)", br.get("iibb")),
                           ("(−) Impuesto a las Ganancias (estimación)", br.get("ganancias")),
                           ("Resultado después de Ganancias", br.get("resultadoDespues"))):
            put(ws, r, 1, label); put(ws, r, 2, val or 0, fmt=MONEY); r += 1
        put(ws, r + 1, 1, br.get("ganancias_nota", ""))
        put(ws, r + 2, 1, br.get("iibb_nota", ""))
    elif reg == "monotributo":
        mt = fz.get("monotributo", {})
        for label, val, fmt in (("Categoría", mt.get("categoria"), None),
                                ("Cuota mensual total", mt.get("cuotaMensualTotal"), MONEY),
                                ("Techo facturación anual (nominal)", mt.get("techoFacturacionAnual"), MONEY),
                                ("Headroom (nominal)", mt.get("headroom"), MONEY),
                                ("Proximidad al techo", mt.get("proximidad"), PCT)):
            put(ws, r, 1, label); put(ws, r, 2, val if val is not None else "—", fmt=fmt); r += 1
    else:
        put(ws, r, 1, "Régimen fiscal no configurado (definir fiscal.regimen).")
    _set_col_width(ws, 1, 38); _set_col_width(ws, 2, 20)
    return ws


# ---------------------------------------------------------------------------
# Tab — Palancas / Acciones
# ---------------------------------------------------------------------------

def _build_palancas(wb, results):
    lv = (results or {}).get("levers") or {}
    ws = wb.create_sheet("Palancas")
    ws.sheet_properties.tabColor = "B08858"
    put(ws, 1, 1, "Palancas / Acciones — impactos NO aditivos (no sumar).",
        font=Font(bold=True, color="6B2532"))
    for col, h in enumerate(["Prioridad", "Palanca", "Acción", "Impacto/mes (real)",
                             "Confianza", "Driver", "Supuesto"], 1):
        put(ws, 3, col, h)
    header(ws, 3)
    row = 4
    for l in lv.get("levers", []):
        put(ws, row, 1, l.get("prioridad"))
        put(ws, row, 2, l.get("titulo"))
        put(ws, row, 3, l.get("accion"))
        put(ws, row, 4, (l.get("impacto") or {}).get("real", 0), fmt=MONEY)
        put(ws, row, 5, l.get("confianza"))
        put(ws, row, 6, l.get("driver"))
        put(ws, row, 7, l.get("supuesto"))
        row += 1
    if row == 4:
        put(ws, 4, 1, "Sin palancas accionables: indicadores dentro de rango.")
    put(ws, row + 1, 1, lv.get("nota", "Impactos no aditivos."))
    for c, w in ((1, 9), (2, 28), (3, 38), (4, 18), (5, 11), (6, 12), (7, 44)):
        _set_col_width(ws, c, w)
    return ws


# ---------------------------------------------------------------------------
# Tab — Supuestos
# ---------------------------------------------------------------------------

def _build_supuestos(wb, fin):
    ws = wb.create_sheet("Supuestos")
    ws.sheet_properties.tabColor = "61574A"
    fz = fin.get("fiscal") or {}
    notas = [
        "Estados leídos del workbook y conciliados (no recalculados).",
        f"Reexpresión a moneda de cierre {fin.get('baseMonth') or 'n/d'} vía IPC INDEC nivel general — "
        "homogeneización del Estado de Resultados.",
        "RECPAM (Resultado por Exposición a la Inflación) FUERA DE ALCANCE — requiere balance completo "
        "con partidas monetarias/no monetarias.",
        f"Posición fiscal sobre pesos nominales (base AFIP); régimen: {fz.get('regimen') or 'no configurado'}. "
        "Ganancias = estimación por alícuota efectiva, no liquidación.",
        "Palancas estimadas de forma independiente: NO son aditivas.",
    ]
    put(ws, 1, 1, "Supuestos y notas metodológicas", font=Font(bold=True, color="6B2532", size=12))
    for i, n in enumerate(notas, start=3):
        put(ws, i, 1, "• " + n)
    _set_col_width(ws, 1, 100)
    return ws


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def write_xlsx(fin, results, out_path):
    wb = openpyxl.Workbook()

    # Remove default sheet
    default = wb.active
    wb.remove(default)

    _build_resumen(wb, fin, results)
    _build_estado(wb, fin)
    _build_reexpresion(wb, fin)
    _build_flujo(wb, fin, results)
    _build_fiscal(wb, fin)
    _build_variacion(wb, results)
    _build_palancas(wb, results)
    _build_ratios(wb, results)
    _build_proyeccion(wb, results)
    _build_supuestos(wb, fin)
    _build_advertencias(wb, fin)

    wb.save(out_path)
    return out_path
