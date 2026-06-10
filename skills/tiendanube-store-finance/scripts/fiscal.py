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

def ri_bridge(resultado_antes, ventas, compras_gravadas, cfg):
    iibb = ventas * cfg.get("alicuotaIIBB", 0.0)
    base_gan = resultado_antes - iibb
    ganancias = max(0.0, base_gan) * cfg.get("alicuotaEfectivaGanancias", 0.0)
    return {
        "iibb": iibb,
        "ganancias": ganancias,
        "ganancias_nota": "Estimación por alícuota efectiva — no es una liquidación de Ganancias.",
        "resultadoDespues": resultado_antes - iibb - ganancias,
    }

def monotributo_status(categoria, facturacion_anual_nominal, tables):
    cats = tables["monotributo"]["categorias"]
    techo_max = max(c["techoFacturacionAnual"] for c in cats.values())
    if facturacion_anual_nominal > techo_max:
        raise ValueError(
            f"Facturación anual nominal {facturacion_anual_nominal:,.0f} supera el techo máximo "
            f"de Monotributo ({techo_max:,.0f}): el contribuyente quedaría EXCLUIDO. "
            f"Configurar régimen 'responsable_inscripto'.")
    c = cats[categoria]
    techo = c["techoFacturacionAnual"]
    return {
        "categoria": categoria,
        "cuotaMensualTotal": c["cuotaMensualTotal"],
        "techoFacturacionAnual": techo,
        "headroom": techo - facturacion_anual_nominal,
        "proximidad": (facturacion_anual_nominal / techo) if techo else 0.0,
        "resolucion": tables["monotributo"].get("resolucion"),
    }
