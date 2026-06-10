"""The schema-2.0 monetary measure: nominal + real + provenance.

Every money figure in the canonical model is a measure. `real` is filled by the
restatement layer (reexpresión a moneda de cierre); None until then. `transforms`
is a SET (order-preserving, deduped) so no figure is restated twice.
"""

def measure(nominal, real=None, source="fact", transforms=None):
    return {
        "nominal": float(nominal),
        "real": (None if real is None else float(real)),
        "source": source,
        "transforms": list(dict.fromkeys(transforms or [])),
    }

def fact(nominal):
    return measure(nominal, source="fact")

def derived(nominal, real=None, transforms=None):
    return measure(nominal, real=real, source="derived", transforms=transforms)

def nom(x):
    """Nominal value of a measure or a bare scalar (back-compat)."""
    if isinstance(x, dict) and "nominal" in x:
        return x["nominal"]
    return float(x)

def real_or_nom(x):
    """Real value if restated, else nominal. Accepts measure or scalar."""
    if isinstance(x, dict) and "nominal" in x:
        return x["real"] if x.get("real") is not None else x["nominal"]
    return float(x)

def add_transform(m, name):
    """Return a copy of measure m with `name` added to transforms (deduped)."""
    return {**m, "transforms": list(dict.fromkeys([*m["transforms"], name]))}
