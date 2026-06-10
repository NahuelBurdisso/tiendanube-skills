"""Assemble the canonical financials.json from parsed workbook blocks."""
from measures import fact, nom
from labels import MONTHS, normalize

SCHEMA_VERSION = "2.0"

_MONTH_NUM = {normalize(m): i + 1 for i, m in enumerate(MONTHS)}

def _sum(xs): return float(sum(nom(x) for x in xs)) if xs else 0.0

def _month_keys(months, year):
    """Map Spanish month names + year -> 'YYYY-MM' keys for IPC lookup.
    None per slot when the year is unlabeled or a month name doesn't resolve —
    restatement then degrades that month to nominal-only with a warning."""
    if not year:
        return [None] * len(months)
    keys = []
    for m in months:
        num = _MONTH_NUM.get(normalize(m))
        keys.append(f"{int(year):04d}-{num:02d}" if num else None)
    return keys

def build_financials(parsed, currency="ARS", store_name=None):
    raw = parsed["incomeStatement"]["monthly"]
    m = {k: [fact(v or 0) for v in series] for k, series in raw.items()}
    annual = {k: fact(_sum(series)) for k, series in m.items()}
    ventas = nom(annual.get("ventas", fact(0.0)))
    annual["margenBruto"] = (nom(annual.get("utilidadBruta", fact(0.0))) / ventas) if ventas else 0.0
    annual["margenNeto"] = (nom(annual.get("utilidadNeta", fact(0.0))) / ventas) if ventas else 0.0
    ventas_series = raw.get("ventas", [])
    active = 0
    for i, v in enumerate(ventas_series):
        if v:
            active = i + 1
    annualized_ventas = (nom(annual.get("ventas", fact(0.0))) / active * 12) if active else 0.0
    # cash-flow lines become measures too, so the restatement layer can fill their `real`.
    # break-even margen bruto stays a ratio (not money) — never restated.
    cf_raw = parsed["cashFlow"]["monthly"]
    cash_flow = {"monthly": {k: [fact(v or 0) for v in series] for k, series in cf_raw.items()}}
    # break-even safety margin — only when the workbook actually fills "facturación necesaria".
    # If it's blank/0, margenSeguridad stays None (unknown) — never a misleading 100% cushion.
    be = dict(parsed.get("breakEven", {}))
    fe_annual = float(sum(be.get("facturacionEquilibrioMonthly", []) or []))
    if fe_annual > 0 and ventas > 0:
        be["facturacionEquilibrioAnual"] = fe_annual
        be["margenSeguridad"] = (ventas - fe_annual) / ventas
        _SAFE_TARGET = 0.20
        be["facturacionParaColchon"] = max(0.0, fe_annual / (1 - _SAFE_TARGET) - ventas)
    else:
        be["facturacionEquilibrioAnual"] = fe_annual or None
        be["margenSeguridad"] = None
        be["facturacionParaColchon"] = None
    return {
        "schemaVersion": SCHEMA_VERSION,
        "baseMonth": None,
        "source": "workbook",
        "storeName": store_name,
        "currency": currency,
        "months": parsed["months"],
        "monthKeys": _month_keys(parsed["months"], parsed.get("year")),
        "year": parsed.get("year"),
        "activeMonths": active,
        "annualizedVentas": annualized_ventas,
        "incomeStatement": {"monthly": m, "annual": annual},
        "cashFlow": cash_flow,
        "breakEven": be,
        "balanceSheetPartial": {"inventory": None, "accountsReceivable": None,
                                "accountsPayable": None},
        "drivers": {"topProducts": []},
        "warnings": list(parsed.get("warnings", [])),
    }
