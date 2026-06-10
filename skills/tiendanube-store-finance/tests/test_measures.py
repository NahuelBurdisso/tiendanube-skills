import importlib.util, pathlib
spec = importlib.util.spec_from_file_location(
    "measures", pathlib.Path(__file__).parent.parent / "scripts" / "measures.py")
measures = importlib.util.module_from_spec(spec); spec.loader.exec_module(measures)

def test_fact_is_nominal_only():
    m = measures.fact(100)
    assert m == {"nominal": 100.0, "real": None, "source": "fact", "transforms": []}

def test_derived_carries_transforms():
    m = measures.derived(80, transforms=["taxed"])
    assert m["source"] == "derived" and m["transforms"] == ["taxed"] and m["nominal"] == 80.0

def test_nom_unwraps_measure_or_scalar():
    assert measures.nom(measures.fact(42)) == 42.0
    assert measures.nom(42) == 42.0

def test_real_or_nom_falls_back_to_nominal_when_real_absent():
    assert measures.real_or_nom(measures.fact(42)) == 42.0
    m = measures.measure(100, real=130)
    assert measures.real_or_nom(m) == 130.0

def test_transforms_dedupe_on_add():
    m = measures.fact(10)
    m2 = measures.add_transform(measures.add_transform(m, "restated"), "restated")
    assert m2["transforms"] == ["restated"]   # idempotent, no double-restate
