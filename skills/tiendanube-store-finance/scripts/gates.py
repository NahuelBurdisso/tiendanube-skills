"""Mandatory data-integrity gates. Hard failures raise GateError; soft issues warn."""
from measures import nom

class GateError(Exception):
    pass

TOL_ABS = 1.0
TOL_REL = 0.001

def gate_tieout(fin):
    """Computed annual vs the workbook's own TOTAL/Anual column when captured
    (the real tie-out); falls back to Σ of the monthlies when the column is absent."""
    is_ = fin["incomeStatement"]
    a = is_["annual"]; m = is_["monthly"]
    wb = is_.get("annualFromWorkbook") or {}
    for key in ("ventas",):
        annual = nom(a[key])
        if wb.get(key) is not None:
            ref, src = float(wb[key]), "TOTAL del workbook"
        else:
            ref, src = sum(nom(x) for x in m[key]), "Σ mensual"
        if abs(annual - ref) > max(TOL_ABS, TOL_REL * abs(ref)):
            raise GateError(f"Tie-out {key}: anual {annual} ≠ {src} {ref}.")

def gate_composition(fin):
    """No figure may carry a duplicated transform (e.g. restated twice). Scans the
    income statement (monthly + annual) and the cash flow."""
    blocks = [fin.get("incomeStatement", {}).get("monthly", {}),
              fin.get("incomeStatement", {}).get("annual", {}),
              fin.get("cashFlow", {}).get("monthly", {})]
    for block in blocks:
        for v in block.values():
            for x in (v if isinstance(v, list) else [v]):
                if isinstance(x, dict):
                    t = x.get("transforms", [])
                    if len(t) != len(set(t)):
                        raise GateError("Composición: una partida fue reexpresada dos veces "
                                        "(transforms duplicados).")

def gate_reexpresion(fin):
    if fin.get("baseMonth") is None:
        # not fatal on its own — restatement already warned; surface, don't raise
        fin.setdefault("warnings", []).append(
            "Reexpresión no disponible (baseMonth nulo): se reportan valores nominales.")

def gate_fiscal(fin):
    f = fin.get("fiscal")
    if not isinstance(f, dict) or "regimen" not in f:
        raise GateError("Fiscal: bloque fiscal ausente o sin 'regimen'.")

def run_all(fin, cfg):
    """Hard gates raise; soft gates append warnings. Returns the model."""
    gate_tieout(fin)
    gate_composition(fin)
    gate_reexpresion(fin)
    gate_fiscal(fin)
    return fin
