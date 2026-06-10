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


# ---------------------------------------------------------------------------
# Task 2 — real-terms margin & real-decline rules
# ---------------------------------------------------------------------------

from measures import measure, fact


def _model_margins(real_series):
    ventas = [measure(v*3, real=v*3) for v in [100, 100, 100]]
    ub = [measure(0, real=r) for r in real_series]
    return {"incomeStatement": {"monthly": {"ventas": ventas, "utilidadBruta": ub},
                                "annual": {"ventas": measure(900, real=900), "margenBruto": 0.30}},
            "baseMonth": "2026-03"}


def test_margin_erosion_fires_in_real_terms():
    m = _model_margins([90, 80, 70])
    lev = levers.rule_margen_erosionado(m, {"finance": {"umbrales": {}}})
    assert lev is not None and lev["driver"] == "margen"
    assert lev["impacto"]["real"] > 0
    assert "real" in lev["supuesto"].lower() or "moneda" in lev["supuesto"].lower()


def test_margin_stable_does_not_fire():
    m = _model_margins([90, 90, 90])
    assert levers.rule_margen_erosionado(m, {"finance": {"umbrales": {}}}) is None


def test_real_decline_uses_explicit_counterfactual():
    ventas = [measure(100, real=100), measure(120, real=95)]
    m = {"incomeStatement": {"monthly": {"ventas": ventas}, "annual": {}}, "baseMonth": "2026-02"}
    lev = levers.rule_caida_real(m, {"finance": {}})
    assert lev is not None and "constante" in lev["supuesto"].lower()


# ---------------------------------------------------------------------------
# Task 3 — Monotributo (nominal), existencias, break-even rules
# ---------------------------------------------------------------------------

def test_monotributo_lever_reads_nominal_block():
    model = {"fiscal": {"regimen": "monotributo", "monotributo": {
        "categoria": "H", "headroom": 400000, "proximidad": 0.94, "techoFacturacionAnual": 9000000}},
        "incomeStatement": {"monthly": {}, "annual": {}}}
    lev = levers.rule_monotributo_limite(model, {"finance": {}})
    assert lev is not None and lev["driver"] == "fiscal"
    assert lev["impacto"]["nominal"] == 400000
    assert "nominal" in lev["supuesto"].lower()


def test_monotributo_lever_silent_when_far():
    model = {"fiscal": {"regimen": "monotributo", "monotributo": {
        "categoria": "A", "headroom": 8000000, "proximidad": 0.2, "techoFacturacionAnual": 9000000}},
        "incomeStatement": {"monthly": {}, "annual": {}}}
    assert levers.rule_monotributo_limite(model, {"finance": {}}) is None


def test_existencias_uses_recoverable_value_low_confidence():
    model = {"balanceSheetPartial": {"inventory": 500000},
             "drivers": {"slowMovingValue": 200000, "recoverableRate": 0.6},
             "incomeStatement": {"monthly": {}, "annual": {}}}
    lev = levers.rule_existencias_inmovilizadas(model, {"finance": {}})
    assert lev is not None and lev["confianza"] == "baja"
    assert lev["impacto"]["real"] == 120000


def test_colchon_fires_when_margin_of_safety_thin():
    model = {"breakEven": {"margenSeguridad": 0.05, "facturacionParaColchon": 30000},
             "incomeStatement": {"monthly": {}, "annual": {}}}
    lev = levers.rule_colchon_equilibrio(model, {"finance": {}})
    assert lev is not None and lev["driver"] == "equilibrio" and lev["impacto"]["real"] == 30000

def test_colchon_silent_when_cushion_ok():
    model = {"breakEven": {"margenSeguridad": 0.5}, "incomeStatement": {"monthly": {}, "annual": {}}}
    assert levers.rule_colchon_equilibrio(model, {"finance": {}}) is None
