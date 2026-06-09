"""Surface only ratios computable for a private retailer with no debt/equity/market data.
ratio_calculator.py emits {categories:{<cat>:{<key>:{value,formula,name,interpretation}}}}.
Keep profitability/liquidity/efficiency; drop the leverage + valuation categories
entirely, and drop any ratio flagged 'Insufficient data to calculate'.
Returns a flat {ratio_key: value}."""
SURFACED_CATEGORIES = {"profitability", "liquidity", "efficiency"}
INSUFFICIENT = "Insufficient data to calculate"

def filter_ratios(raw):
    out = {}
    cats = raw.get("categories", {}) if isinstance(raw, dict) else {}
    for cat, ratios in cats.items():
        if cat not in SURFACED_CATEGORIES:
            continue
        for key, info in (ratios or {}).items():
            if isinstance(info, dict):
                if info.get("interpretation") == INSUFFICIENT:
                    continue
                out[key] = info.get("value")
            else:
                out[key] = info
    return out
