"""Superscript provenance marks tying report figures to the methodology appendix."""
_MARK = {"restated": "ʳ", "taxed": "ᵗ", "assumption": "ˢ", "projected": "ᵖ"}
_DESC = {"restated": "reexpresado a moneda de cierre", "taxed": "impuesto modelado",
         "assumption": "supuesto", "projected": "inflación proyectada"}

def marks(m):
    if not isinstance(m, dict):
        return ""
    return "".join(_MARK[t] for t in m.get("transforms", []) if t in _MARK)

def legend(measures_used):
    seen = []
    for m in measures_used:
        for t in (m.get("transforms", []) if isinstance(m, dict) else []):
            if t in _MARK and t not in seen:
                seen.append(t)
    return " · ".join(f"{_MARK[t]} {_DESC[t]}" for t in seen)
