import importlib.util, pathlib
import pytest

def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

gates = _load("gates")
measures = _load("measures")


def _fin(ventas_monthly, ventas_annual):
    return {"incomeStatement": {"monthly": {"ventas": [measures.fact(v) for v in ventas_monthly]},
                                "annual": {"ventas": measures.fact(ventas_annual)}},
            "activeMonths": len(ventas_monthly),
            "monthKeys": ["2026-0%d" % (i+1) for i in range(len(ventas_monthly))],
            "baseMonth": "2026-03", "warnings": [], "fiscal": {"regimen": "monotributo"}}

def test_tieout_passes_within_tolerance():
    gates.gate_tieout(_fin([100, 100, 100], 300.0))

def test_tieout_fails_outside_tolerance():
    with pytest.raises(gates.GateError):
        gates.gate_tieout(_fin([100, 100, 100], 305.0))

def test_composition_rejects_double_restate():
    m = {**measures.fact(1), "transforms": ["restated", "restated"]}
    with pytest.raises(gates.GateError):
        gates.gate_composition({"incomeStatement": {"monthly": {"ventas": [m]}, "annual": {}}})

def test_run_all_passes_clean_model():
    fin = _fin([100, 100, 100], 300.0)
    out = gates.run_all(fin, {})
    assert out is fin            # returns the model

def test_fiscal_gate_requires_regimen_key():
    fin = _fin([100], 100.0); fin["fiscal"] = {}
    with pytest.raises(gates.GateError):
        gates.gate_fiscal(fin)
