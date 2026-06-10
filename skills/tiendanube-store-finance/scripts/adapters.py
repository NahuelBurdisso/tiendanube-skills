"""Map canonical financials -> each vendored script's required input JSON.
financial-analyst AUGMENTS the read statements; it never recomputes them."""
from measures import nom

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
    active = fin.get("activeMonths") or len(m["ventas"])
    ventas = [nom(v) for v in m["ventas"][:active]]
    # everything below gross profit: fixed + amortization + variable expenses
    opex = (nom(a.get("gastosVariables", 0.0)) + nom(a.get("costosFijos", 0.0)) + nom(a.get("amortizacion", 0.0)))
    a_ventas = nom(a.get("ventas", 0.0))
    opex_pct = (opex / a_ventas) if a_ventas else 0.0
    fin_cfg = cfg.get("finance", cfg)  # tolerate flat or nested config
    # weekly cash-flow inputs must reflect the RUN-RATE, not the YTD total: annualize
    # YTD figures by active months so a partial year doesn't understate the projection.
    ann = (12.0 / active) if active else 1.0
    def _weekly(x): return x * ann / 52.0
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
            "weekly_revenue": _weekly(a_ventas),
            "collection_rate": fin_cfg.get("collectionRate", 1.0),
            "payroll": fin_cfg.get("payrollWeekly", _weekly(nom(a.get("costosFijos", 0.0)))),
            "rent": fin_cfg.get("rentWeekly", 0),
            "operating_expenses": _weekly(opex),
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
    totals = fin["cashFlow"]["monthly"].get("total", []) or [0]
    active = fin.get("activeMonths") or len(totals)
    cash = sum(totals[:active])            # net operating cash generated in the period
    op_income = nom(a.get("utilidadOperativa", 0.0))
    a_ventas = nom(a.get("ventas", 0.0))
    return {
        "income_statement": {
            "revenue": a_ventas,
            # effective COGS = revenue - gross profit (includes Comisiones), so the
            # ratio's gross margin reconciles to the statement's margenBruto
            "cost_of_goods_sold": a_ventas - nom(a.get("utilidadBruta", 0.0)),
            "operating_income": op_income,
            "net_income": nom(a.get("utilidadNeta", 0.0)),
            "ebitda": op_income + nom(a.get("amortizacion", 0.0)),
        },
        "balance_sheet": {
            "inventory": inv,
            "accounts_receivable": ar,
            "cash_and_equivalents": max(0.0, cash),
            "current_assets": inv + ar + max(0.0, cash),
            "current_liabilities": ap,
        },
        "cash_flow": {"operating_cash_flow": cash},  # real cash, not the accrual proxy
        "market_data": {},
    }

_VAR_TYPES = {"ventas": "revenue", "utilidadBruta": "income",
              "utilidadOperativa": "income", "utilidadNeta": "income"}

def to_variance_input(fin, company=None):
    """Period-over-period: actual = last month, prior_year = previous month.
    NO budget exists in the template, so `budget` is omitted."""
    m = fin["incomeStatement"]["monthly"]
    active = fin.get("activeMonths") or len(m.get("ventas", []))
    label = {"ventas": "Ventas", "costoReposicion": "Costo reposición",
             "utilidadBruta": "Utilidad bruta", "utilidadOperativa": "Utilidad operativa",
             "utilidadNeta": "Utilidad neta", "costosFijos": "Costos fijos"}
    items = []
    for key, name in label.items():
        series = m.get(key, [])[:active]
        if len(series) >= 2:
            items.append({
                "name": name,
                "type": _VAR_TYPES.get(key, "expense"),
                "actual": nom(series[-1]),
                "prior_year": nom(series[-2]),  # prior MONTH (period-over-period; the template has no budget)
            })
    return {"company": company or fin.get("storeName") or "Cliente",
            "period": (fin["months"][-1] if fin["months"] else "Actual"),
            "line_items": items}
