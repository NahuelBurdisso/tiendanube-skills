"""Regime-aware fiscal layer, computed on NOMINAL pesos (AFIP basis).

RI: IVA débito/crédito posición (a flujo fiscal, NOT a result line), IIBB gasto,
Ganancias ESTIMACIÓN (alícuota efectiva — not a liquidación). Monotributo: cuota
from categoría; nominal techo proximity. Restatement runs AFTER this, always.
"""
import json, pathlib
from measures import nom, derived

def load_fiscal_tables(ref_dir=None):
    ref_dir = pathlib.Path(ref_dir) if ref_dir else pathlib.Path(__file__).parent.parent / "reference"
    return json.loads((ref_dir / "tablas-fiscales-ar.json").read_text())

def iva_position(ventas, compras_gravadas, alicuota):
    debito = ventas * alicuota
    credito = compras_gravadas * alicuota
    return {"debito": debito, "credito": credito, "posicion": debito - credito}
