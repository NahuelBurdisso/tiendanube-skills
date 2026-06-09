"""Map canonical financials -> each vendored script's required input JSON.
financial-analyst AUGMENTS the read statements; it never recomputes them."""

def _avg_growth(series):
    rates = []
    for i in range(1, len(series)):
        prev = series[i-1]
        if prev:
            rates.append((series[i] - prev) / prev)
    return sum(rates) / len(rates) if rates else 0.0

def to_forecast_input(fin, cfg):
    m = fin["incomeStatement"]["monthly"]
    a = fin["incomeStatement"]["annual"]
    ventas = m["ventas"]
    opex = (a.get("gastosVariables", 0.0) + a.get("costosFijos", 0.0))
    opex_pct = (opex / a["ventas"]) if a.get("ventas") else 0.0
    fin_cfg = cfg.get("finance", cfg)  # tolerate flat or nested config
    return {
        "historical_periods": [{"revenue": v} for v in ventas],
        "drivers": {"units": {}, "pricing": {}},
        "assumptions": {
            "revenue_growth_rate": _avg_growth(ventas),
            "gross_margin": a.get("margenBruto", 0.0),
            "opex_pct_revenue": opex_pct,
        },
        "cash_flow_inputs": {
            "opening_balance": fin_cfg.get("cashBalance", 0),
            "weekly_revenue": (a.get("ventas", 0.0) / 52.0),
            "collection_rate": fin_cfg.get("collectionRate", 1.0),
            "payroll": fin_cfg.get("payrollWeekly", a.get("costosFijos", 0.0) / 52.0),
            "rent": fin_cfg.get("rentWeekly", 0),
            "operating_expenses": (opex / 52.0),
        },
        "scenarios": cfg.get("scenarios", {
            "base": {"growth_adjustment": 0.0, "margin_adjustment": 0.0},
            "bull": {"growth_adjustment": 0.05, "margin_adjustment": 0.02},
            "bear": {"growth_adjustment": -0.05, "margin_adjustment": -0.02}}),
        "forecast_periods": cfg.get("forecastPeriods", 12),
    }

def to_ratios_input(fin):
    a = fin["incomeStatement"]["annual"]
    bsp = fin["balanceSheetPartial"]
    inv = bsp.get("inventory") or 0
    ar = bsp.get("accountsReceivable") or 0
    ap = bsp.get("accountsPayable") or 0
    cash = (fin["cashFlow"]["monthly"]["total"] or [0])[-1] or 0
    op_income = a.get("utilidadOperativa", 0.0)
    return {
        "income_statement": {
            "revenue": a.get("ventas", 0.0),
            # effective COGS = revenue - gross profit (includes Comisiones), so the
            # ratio's gross margin reconciles to the statement's margenBruto
            "cost_of_goods_sold": a.get("ventas", 0.0) - a.get("utilidadBruta", 0.0),
            "operating_income": op_income,
            "net_income": a.get("utilidadNeta", 0.0),
            "ebitda": op_income + a.get("amortizacion", 0.0),
        },
        "balance_sheet": {
            "inventory": inv,
            "accounts_receivable": ar,
            "cash_and_equivalents": cash,
            "current_assets": inv + ar + cash,
            "current_liabilities": ap,
        },
        "cash_flow": {"operating_cash_flow": op_income},
        "market_data": {},
    }

_VAR_TYPES = {"ventas": "revenue", "utilidadBruta": "income",
              "utilidadOperativa": "income", "utilidadNeta": "income"}

def to_variance_input(fin, company=None):
    """Period-over-period: actual = last month, prior_year = previous month.
    NO budget exists in the template, so `budget` is omitted."""
    m = fin["incomeStatement"]["monthly"]
    label = {"ventas": "Ventas", "costoReposicion": "Costo reposición",
             "utilidadBruta": "Utilidad bruta", "utilidadOperativa": "Utilidad operativa",
             "utilidadNeta": "Utilidad neta", "costosFijos": "Costos fijos"}
    items = []
    for key, name in label.items():
        series = m.get(key, [])
        if len(series) >= 2:
            items.append({
                "name": name,
                "type": _VAR_TYPES.get(key, "expense"),
                "actual": series[-1],
                "prior_year": series[-2],
            })
    return {"company": company or fin.get("storeName") or "Cliente",
            "period": (fin["months"][-1] if fin["months"] else "Actual"),
            "line_items": items}
