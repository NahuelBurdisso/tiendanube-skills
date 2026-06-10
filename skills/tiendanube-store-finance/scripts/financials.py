"""Assemble the canonical financials.json from parsed workbook blocks."""
from measures import fact, nom

SCHEMA_VERSION = "2.0"

def _sum(xs): return float(sum(nom(x) for x in xs)) if xs else 0.0

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
    return {
        "schemaVersion": SCHEMA_VERSION,
        "baseMonth": None,
        "source": "workbook",
        "storeName": store_name,
        "currency": currency,
        "months": parsed["months"],
        "year": parsed.get("year"),
        "activeMonths": active,
        "annualizedVentas": annualized_ventas,
        "incomeStatement": {"monthly": m, "annual": annual},
        "cashFlow": parsed["cashFlow"],
        "breakEven": parsed["breakEven"],
        "balanceSheetPartial": {"inventory": None, "accountsReceivable": None,
                                "accountsPayable": None},
        "drivers": {"topProducts": []},
        "warnings": list(parsed.get("warnings", [])),
    }
