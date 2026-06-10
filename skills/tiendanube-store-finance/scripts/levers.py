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


# ---------------------------------------------------------------------------
# Helpers shared by all rules
# ---------------------------------------------------------------------------

from measures import real_or_nom


def _real_series(model, key):
    s = model["incomeStatement"]["monthly"].get(key, [])
    return [m["real"] for m in s if isinstance(m, dict) and m.get("real") is not None]


def _mk(idd, titulo, driver, disparador, accion, impacto_real, supuesto, conf):
    return {"id": idd, "titulo": titulo, "driver": driver, "disparador": disparador,
            "accion": accion, "impacto": {"nominal": impacto_real, "real": impacto_real},
            "supuesto": supuesto, "confianza": conf, "prioridad": None}


# ---------------------------------------------------------------------------
# Task 2 rules
# ---------------------------------------------------------------------------

def rule_margen_erosionado(model, cfg):
    ub = _real_series(model, "utilidadBruta")
    if len(ub) < 2 or ub[0] == 0 or ub[-1] >= ub[0]:
        return None
    impacto = ub[0] - ub[-1]
    return _mk("margen-bruto-erosionado", "Recuperar margen bruto (términos reales)",
               "margen", {"metric": "utilidadBruta.real", "inicio": ub[0], "fin": ub[-1]},
               "Subir precio por encima de inflación o renegociar CMV.",
               impacto, "Volumen constante; medido en moneda de cierre (real).", "media")


def rule_caida_real(model, cfg):
    v = model["incomeStatement"]["monthly"].get("ventas", [])
    if len(v) < 2:
        return None
    nom0, nomN = v[0]["nominal"], v[-1]["nominal"]
    real0, realN = real_or_nom(v[0]), real_or_nom(v[-1])
    if not (nomN > nom0 and realN < real0):
        return None
    impacto = real0 - realN
    return _mk("caida-terminos-reales", "Ventas crecen en pesos pero caen en términos reales",
               "ventas", {"metric": "ventas.real", "inicio": real0, "fin": realN},
               "Las subas de precio no compensan inflación; revisar volumen/mix.",
               impacto, "Pérdida vs. mantener el resultado real constante.", "alta")


RULES += [rule_margen_erosionado, rule_caida_real]
