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
