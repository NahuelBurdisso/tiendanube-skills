"""Write store-finance.xlsx. The Estado de Resultados tab MUST tie out to the
client's workbook (we reproduce the read values, never recomputed)."""
import openpyxl

_IS_ROWS = [("ventas","Ventas"),("costoReposicion","Costo reposición"),
            ("comisiones","Comisiones"),("utilidadBruta","Utilidad bruta"),
            ("costosFijos","Costos fijos"),("amortizacion","Amortización créditos"),
            ("utilidadOperativa","Utilidad operativa"),
            ("gastosVariables","Gastos variables"),("utilidadNeta","Utilidad neta")]

def write_xlsx(fin, results, out_path):
    wb = openpyxl.Workbook()
    # --- Estado de Resultados (reconciled) ---
    ws = wb.active; ws.title = "Estado de Resultados"
    months = fin["months"]
    ws.append(["Concepto"] + months + ["Anual"])
    m = fin["incomeStatement"]["monthly"]; a = fin["incomeStatement"]["annual"]
    for key, label in _IS_ROWS:
        ws.append([label] + m.get(key, []) + [a.get(key, 0.0)])
    ws.append([]); ws.append(["Margen bruto", a.get("margenBruto", 0.0)])
    ws.append(["Margen neto", a.get("margenNeto", 0.0)])
    # --- Ratios (only surfaced) ---
    rt = wb.create_sheet("Ratios")
    rt.append(["Ratio", "Valor"])
    for k, v in (results.get("ratios") or {}).items():
        rt.append([k, v])
    # --- Forecast (scenarios summary if present) ---
    fc = wb.create_sheet("Forecast")
    fc.append(["Forecast (resumen)"])
    forecast = results.get("forecast") or {}
    for k in ("trend_analysis", "scenario_comparison", "rolling_cash_flow"):
        if k in forecast:
            fc.append([k, str(forecast[k])[:5000]])
    # --- Variance (period-over-period) ---
    vt = wb.create_sheet("Variance (período)")
    vt.append(["Concepto", "Actual", "Período previo", "Δ", "Δ%"])
    for li in (results.get("variance") or {}).get("line_items", []):
        act, pri = li.get("actual", 0), li.get("prior_year", 0)
        d = act - (pri or 0); dp = (d / pri) if pri else 0
        vt.append([li.get("name"), act, pri, d, dp])
    wb.save(out_path)
    return out_path
