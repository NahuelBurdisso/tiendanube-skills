"""Regime-aware fiscal layer, computed on NOMINAL pesos (AFIP basis).

RI: IVA débito/crédito posición (a flujo fiscal, NOT a result line), IIBB gasto,
Ganancias ESTIMACIÓN (alícuota efectiva — not a liquidación). Monotributo: cuota
from categoría; nominal techo proximity. Restatement runs AFTER this, always.
"""
import json, pathlib
from measures import nom

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

def monotributo_status(categoria, facturacion_anual_nominal, tables, raise_on_exclusion=True):
    cats = tables["monotributo"]["categorias"]
    techo_max = max(c["techoFacturacionAnual"] for c in cats.values())
    if raise_on_exclusion and facturacion_anual_nominal > techo_max:
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


def apply_fiscal(fin, cfg, ref_dir=None):
    """Build the fiscal block on NOMINAL pesos and attach it as fin['fiscal'].
    Runs BEFORE restatement (AFIP works in nominal); reexpresión is applied last.
    Tolerates a missing/blank fiscal config — records regimen=None and skips."""
    fcfg = (cfg or {}).get("fiscal", {}) or {}
    regimen = fcfg.get("regimen")
    a = fin["incomeStatement"]["annual"]
    ventas = nom(a.get("ventas", 0.0))
    block = {"regimen": regimen}
    warnings = []

    try:
        tables = load_fiscal_tables(ref_dir)
        block["fuenteTablas"] = tables.get("notas", [None])[0] if isinstance(tables.get("notas"), list) else None
        block["vigenciaHasta"] = tables.get("vigenciaHasta")
    except Exception:
        tables = None
        warnings.append("Tablas fiscales no disponibles: capa fiscal omitida.")

    if regimen == "responsable_inscripto":
        cmv = ventas - nom(a.get("utilidadBruta", 0.0))                 # CMV nominal
        compras_grav = cmv * fcfg.get("proporcionComprasGravadas", 1.0)
        block["iva"] = iva_position(ventas, compras_grav, fcfg.get("alicuotaIVAVentas", 0.21))
        block["iva"]["nota"] = "Posición IVA: flujo fiscal (no integra el Resultado)."
        block["iva"]["fuenteCredito"] = ("crédito estimado como proporción de compras gravadas "
                                         "sobre el CMV; ajustar con el IVA crédito real del workbook.")
        resultado_antes = nom(a.get("utilidadOperativa")) if a.get("utilidadOperativa") else nom(a.get("utilidadNeta", 0.0))
        bridge = ri_bridge(resultado_antes, ventas, compras_grav, fcfg)
        block["bridge"] = bridge
    elif regimen == "monotributo":
        if tables is None:
            warnings.append("Monotributo: sin tablas fiscales, no se evaluó la categoría.")
        else:
            # EXCLUSIÓN (hard error) sobre facturación ACUMULADA REAL (base AFIP), no sobre el
            # run-rate anualizado — un trimestre fuerte no debe "excluir" por extrapolación.
            techo_max = max(c["techoFacturacionAnual"]
                            for c in tables["monotributo"]["categorias"].values())
            if ventas > techo_max:
                raise ValueError(
                    f"Facturación acumulada {ventas:,.0f} supera el techo máximo de Monotributo "
                    f"({techo_max:,.0f}): el contribuyente quedaría EXCLUIDO. "
                    f"Configurar régimen 'responsable_inscripto'.")
            # Proximidad/cuota sobre facturación anualizada (run-rate, prospectivo).
            fact_anual = fin.get("annualizedVentas") or ventas
            block["monotributo"] = monotributo_status(
                fcfg.get("categoriaMonotributo"), fact_anual, tables, raise_on_exclusion=False)
            block["monotributo"]["notaBase"] = (
                "Proximidad sobre facturación anualizada (run-rate); "
                "exclusión evaluada sobre facturación acumulada real.")
    elif regimen:
        warnings.append(f"Régimen fiscal '{regimen}' no reconocido; capa fiscal omitida.")
    # regimen None -> no tax modeling, block records that plainly

    fin["fiscal"] = block
    if warnings:
        fin["warnings"] = list(dict.fromkeys([*fin.get("warnings", []), *warnings]))
    return fin
