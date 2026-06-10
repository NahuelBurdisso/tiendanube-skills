"""Reexpresión a moneda de cierre (P&L homogenization).

Deflates nominal flows to the closing-month currency via IPC INDEC. This is NOT
RT-6/RECPAM (no balance sheet) — it homogenizes the income statement only.
"""
import json, pathlib
from measures import nom, add_transform


def load_ipc(ref_dir=None):
    ref_dir = pathlib.Path(ref_dir) if ref_dir else pathlib.Path(__file__).parent.parent / "reference"
    return json.loads((ref_dir / "ipc-indec.json").read_text())


def coef(serie, base_month, month):
    """IPC(base)/IPC(month); None if either month absent or month index is 0."""
    b = serie.get(base_month); v = serie.get(month)
    if b is None or v is None or v == 0:
        return None
    return b / v


def restate_series(series, months, serie, base_month, projected_inflation=None,
                   last_actual_month=None):
    """Fill `real` on each measure. months[i] aligns with series[i].
    Months past last_actual_month use compounded projected_inflation (tag 'projected').
    Returns (new_series, warnings)."""
    out, warnings = [], []
    for m, meas in zip(months, series):
        c = coef(serie, base_month, m)
        tag = "restated"
        if c is None and projected_inflation is not None and last_actual_month and m > last_actual_month:
            base_idx = serie.get(base_month)
            steps = _months_between(last_actual_month, m)
            proj_idx = serie[last_actual_month] * ((1 + projected_inflation) ** steps)
            c = (base_idx / proj_idx) if (base_idx is not None and proj_idx) else None
            tag = "projected"
        if c is None:
            warnings.append(f"IPC sin dato para {m}: real no calculado (se muestra solo nominal).")
            out.append({**meas, "real": None})
        else:
            out.append(add_transform({**meas, "real": nom(meas) * c}, tag))
    return out, warnings


def _months_between(a, b):
    """Integer month gap b-a for 'YYYY-MM' strings."""
    ay, am = map(int, a.split("-")); by, bm = map(int, b.split("-"))
    return (by * 12 + bm) - (ay * 12 + am)


def _pick_base(month_keys, active, serie, override):
    """Base = moneda de cierre. Config override > closing month of window >
    latest analyzed month present in IPC > None (then everything degrades to nominal)."""
    if override:
        return override
    if active and 0 < active <= len(month_keys):
        closing = month_keys[active - 1]
        if closing in serie:
            return closing
    present = [k for k in month_keys if k in serie]
    return present[-1] if present else None


def restate(fin, fin_cfg=None, ref_dir=None):
    """Fill `real` across the income statement + cash flow, reexpressed to the
    closing-month currency. Sets fin['baseMonth']. Degrades (real=None + warning)
    for any month absent from the IPC series. Break-even margen (a ratio) is left
    untouched. Idempotent via the transforms set."""
    fin_cfg = fin_cfg or {}
    serie = load_ipc(ref_dir)["serie"]
    month_keys = fin.get("monthKeys") or [None] * len(fin.get("months", []))
    active = fin.get("activeMonths") or len(month_keys)
    base = _pick_base(month_keys, active, serie, fin_cfg.get("baseMonth"))
    proj = fin_cfg.get("projectedMonthlyInflation")
    present = [k for k in month_keys if k in serie]
    last_actual = max(present) if present else None
    warnings = []

    def _do(block):
        for key, series in block.items():
            block[key], w = restate_series(series, month_keys, serie, base, proj, last_actual)
            warnings.extend(w)

    is_ = fin["incomeStatement"]
    _do(is_["monthly"])
    # annual real = Σ restated monthly real (null-safe); never nominal × one coef
    for key, series in is_["monthly"].items():
        reals = [x["real"] for x in series if isinstance(x, dict) and x.get("real") is not None]
        ann = is_["annual"].get(key)
        if isinstance(ann, dict):
            is_["annual"][key] = add_transform({**ann, "real": (sum(reals) if reals else None)},
                                               "restated")
    _do(fin["cashFlow"]["monthly"])

    fin["baseMonth"] = base
    if base is None:
        warnings.append("Reexpresión no disponible: sin año etiquetado o meses fuera "
                        "de la serie IPC; se reportan solo valores nominales.")
    # dedupe (every statement line raises the same missing-month warning)
    existing = fin.get("warnings", [])
    fin["warnings"] = list(dict.fromkeys([*existing, *warnings]))
    return fin
