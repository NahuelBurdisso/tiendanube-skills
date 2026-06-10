"""Mandatory data-integrity gates. Hard failures raise GateError; soft issues warn."""
from measures import nom

class GateError(Exception):
    pass

TOL_ABS = 1.0
TOL_REL = 0.001

def gate_tieout(fin):
    a = fin["incomeStatement"]["annual"]; m = fin["incomeStatement"]["monthly"]
    for key in ("ventas",):
        annual = nom(a[key]); summed = sum(nom(x) for x in m[key])
        if abs(annual - summed) > max(TOL_ABS, TOL_REL * abs(summed)):
            raise GateError(f"Tie-out {key}: anual {annual} ≠ Σ mensual {summed}.")

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
