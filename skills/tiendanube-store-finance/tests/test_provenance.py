import importlib.util, pathlib

def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

provenance = _load("provenance")
measures = _load("measures")


def test_marks_for_transforms():
    assert provenance.marks(measures.fact(10)) == ""
    assert "ʳ" in provenance.marks(measures.add_transform(measures.fact(10), "restated"))
    assert "ᵗ" in provenance.marks(measures.derived(8, transforms=["taxed"]))
    assert "ᵖ" in provenance.marks(measures.add_transform(measures.fact(10), "projected"))
    assert "ˢ" in provenance.marks(measures.derived(8, transforms=["assumption"]))

def test_legend_lists_only_used_marks():
    used = [measures.add_transform(measures.fact(1), "restated"), measures.fact(2)]
    leg = provenance.legend(used)
    assert "ʳ" in leg and "reexpresado" in leg.lower()
    assert "ᵗ" not in leg
