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
