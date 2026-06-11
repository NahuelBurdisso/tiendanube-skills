"""Regime-aware fiscal layer, computed on NOMINAL pesos (AFIP basis).

RI: IVA débito/crédito posición (a flujo fiscal, NOT a result line), IIBB gasto,
Ganancias ESTIMACIÓN (alícuota efectiva — not a liquidación). Monotributo: cuota
from categoría; nominal techo proximity. Restatement runs AFTER this, always.
"""
import datetime, json, pathlib
from measures import nom

def load_fiscal_tables(ref_dir=None):
    ref_dir = pathlib.Path(ref_dir) if ref_dir else pathlib.Path(__file__).parent.parent / "reference"
    return json.loads((ref_dir / "tablas-fiscales-ar.json").read_text())

def iva_position(ventas, compras_gravadas, alicuota):
    debito = ventas * alicuota
    credito = compras_gravadas * alicuota
    return {"debito": debito, "credito": credito, "posicion": debito - credito}

def ri_bridge(resultado_neto, ventas, compras_gravadas, cfg):
    """Post-tax bridge from the workbook's RESULTADO NETO (its pre-national-tax bottom line).
    Ganancias is estimated on the net result and subtracted. IIBB is reported for context but
    NOT re-subtracted by default — in a managerial workbook it is usually already inside the
    operating costs; subtracting it again would double-count. Flagged for the contador to confirm."""
    iibb = ventas * cfg.get("alicuotaIIBB", 0.0)
    ganancias = max(0.0, resultado_neto) * cfg.get("alicuotaEfectivaGanancias", 0.0)
    return {
        "resultadoAntes": resultado_neto,
        "iibb": iibb,
        "iibb_nota": ("IIBB estimado sobre ventas. Verificar si ya está incluido en los costos del "
                      "workbook; si lo está, no restarlo de nuevo (evita doble cómputo)."),
        "ganancias": ganancias,
        "ganancias_nota": "Estimación por alícuota efectiva sobre el resultado neto — no es una liquidación de Ganancias.",
        "resultadoDespues": resultado_neto - ganancias,
    }

def monotributo_status(categoria, facturacion_anual_nominal, tables, raise_on_exclusion=True):
    cats = tables["monotributo"]["categorias"]
    techo_max = max(c["techoFacturacionAnual"] for c in cats.values())
    if raise_on_exclusion and facturacion_anual_nominal > techo_max:
        raise ValueError(
            f"Facturación anual nominal {facturacion_anual_nominal:,.0f} supera el techo máximo "
            f"de Monotributo ({techo_max:,.0f}): el contribuyente quedaría EXCLUIDO. "
            f"Configurar régimen 'responsable_inscripto'.")
    c = cats.get(categoria)
    if c is None:
        raise ValueError(f"categoriaMonotributo {categoria!r} inválida; "
                         f"usar {min(cats)}..{max(cats)}.")
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
        block["fuenteTablas"] = "reference/tablas-fiscales-ar.json (ARCA Monotributo + IIBB)"
        block["vigenciaHasta"] = tables.get("vigenciaHasta")
    except Exception:
        tables = None
        warnings.append("Tablas fiscales no disponibles: capa fiscal omitida.")

    # vigencia: warn when the analyzed window (or today) is past the tables' validity
    vig = tables.get("vigenciaHasta") if tables else None
    if vig:
        active = fin.get("activeMonths")
        keys = [k for k in (fin.get("monthKeys") or [])[:active or None] if k]
        last_month = max(keys) if keys else None
        today = datetime.date.today().isoformat()
        if (last_month and last_month > vig[:7]) or today > vig:
            warnings.append(
                f"Tablas fiscales vigentes hasta {vig}: el período analizado o la fecha "
                f"actual la exceden — refrescar Monotributo/IIBB desde ARCA/INDEC antes "
                f"de confiar en la capa fiscal.")

    if regimen == "responsable_inscripto":
        cmv = ventas - nom(a.get("utilidadBruta", 0.0))                 # CMV nominal
        compras_grav = cmv * fcfg.get("proporcionComprasGravadas", 1.0)
        block["iva"] = iva_position(ventas, compras_grav, fcfg.get("alicuotaIVAVentas", 0.21))
        block["iva"]["nota"] = "Posición IVA: flujo fiscal (no integra el Resultado)."
        block["iva"]["fuenteCredito"] = ("crédito estimado como proporción de compras gravadas "
                                         "sobre el CMV; ajustar con el IVA crédito real del workbook.")
        # Bridge from the workbook's RESULTADO NETO (its bottom line), not from operativa —
        # operativa would skip gastos variables/amortización and overstate the post-tax base.
        resultado_neto = nom(a.get("utilidadNeta", 0.0))
        bridge = ri_bridge(resultado_neto, ventas, compras_grav, fcfg)
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
