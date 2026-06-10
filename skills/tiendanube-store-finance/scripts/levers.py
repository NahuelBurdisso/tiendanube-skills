"""Quantified action levers. Each rule is pure (model, cfg) -> lever | None.

Levers read REAL measures and report impact in real terms (a sub-inflation nominal
price rise is a real CUT, never a gain). Impacts are NOT additive across overlapping
drivers — the engine groups by driver and never prints a grand total.
"""
NOTA = ("Impactos no aditivos: cada palanca se estima de forma independiente y "
        "puede solaparse con otras del mismo driver. No sumar.")

def build_levers(model, cfg, rules=None):
    rules = rules if rules is not None else RULES
    found = [r(model, cfg) for r in rules]
    found = [l for l in found if l is not None]
    found.sort(key=lambda l: l["impacto"]["real"], reverse=True)
    for i, l in enumerate(found, 1):
        l["prioridad"] = i
    por_driver = {}
    for l in found:
        por_driver.setdefault(l["driver"], []).append(l)
    return {"levers": found, "porDriver": por_driver, "nota": NOTA}

RULES = []
