"""Assemble the canonical financials.json from parsed workbook blocks."""
SCHEMA_VERSION = "1.0"

def _sum(xs): return float(sum(xs)) if xs else 0.0

def build_financials(parsed, currency="ARS", store_name=None):
    m = parsed["incomeStatement"]["monthly"]
    annual = {k: _sum(v) for k, v in m.items()}
    ventas = annual.get("ventas", 0.0)
    annual["margenBruto"] = (annual.get("utilidadBruta", 0.0) / ventas) if ventas else 0.0
    annual["margenNeto"] = (annual.get("utilidadNeta", 0.0) / ventas) if ventas else 0.0
    return {
        "schemaVersion": SCHEMA_VERSION,
        "source": "workbook",
        "storeName": store_name,
        "currency": currency,
        "months": parsed["months"],
        "incomeStatement": {"monthly": m, "annual": annual},
        "cashFlow": parsed["cashFlow"],
        "breakEven": parsed["breakEven"],
        "balanceSheetPartial": {"inventory": None, "accountsReceivable": None,
                                "accountsPayable": None},
        "drivers": {"topProducts": []},
        "warnings": list(parsed.get("warnings", [])),
    }
