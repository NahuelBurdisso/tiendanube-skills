import importlib.util, pathlib

def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

levers = _load("levers")


# ---------------------------------------------------------------------------
# Task 1 — engine: rank, group-by-driver, no total, null-guard
# ---------------------------------------------------------------------------

def _lever(idd, driver, impact, conf="media"):
    return {"id": idd, "titulo": idd, "driver": driver,
            "disparador": {}, "accion": "", "impacto": {"nominal": impact, "real": impact},
            "supuesto": "", "confianza": conf, "prioridad": None}


def test_engine_ranks_groups_and_never_totals():
    rules = [lambda m, c: _lever("a", "margen", 100),
             lambda m, c: _lever("b", "margen", 50),
             lambda m, c: _lever("c", "stock", 200),
             lambda m, c: None]
    out = levers.build_levers({}, {}, rules=rules)
    assert [l["id"] for l in out["levers"]] == ["c", "a", "b"]
    assert out["levers"][0]["prioridad"] == 1
    assert set(out["porDriver"]) == {"margen", "stock"}
    assert "totalImpacto" not in out and "total" not in out
    assert out["nota"].startswith("Impactos no aditivos")


def test_null_metric_rule_is_skipped():
    rules = [lambda m, c: None]
    assert levers.build_levers({}, {}, rules=rules)["levers"] == []
