import importlib.util, pathlib


def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


restatement = _load("restatement")

IPC = {"2026-01": 100.0, "2026-02": 110.0, "2026-03": 121.0}


def test_coef_base_over_month():
    assert abs(restatement.coef(IPC, "2026-03", "2026-01") - 1.21) < 1e-9   # 121/100
    assert restatement.coef(IPC, "2026-03", "2026-03") == 1.0


def test_missing_month_returns_none():
    assert restatement.coef(IPC, "2026-03", "2026-09") is None


# ---------------------------------------------------------------------------
# Task 2 — restate_series
# ---------------------------------------------------------------------------
from measures import fact  # noqa: E402  (importlib path already inserted by _load above)


def test_restate_series_per_month_and_sum():
    months = ["2026-01", "2026-02", "2026-03"]
    series = [fact(100), fact(100), fact(100)]
    out, warnings = restatement.restate_series(series, months, IPC, base_month="2026-03")
    assert [round(m["real"], 4) for m in out] == [121.0, 110.0, 100.0]   # Jan*1.21, Feb*1.10, Mar*1.0
    assert all("restated" in m["transforms"] for m in out)
    assert warnings == []


def test_restate_missing_month_nulls_and_warns():
    months = ["2026-01", "2026-09"]
    series = [fact(100), fact(100)]
    out, warnings = restatement.restate_series(series, months, IPC, base_month="2026-01")
    assert out[0]["real"] == 100.0
    assert out[1]["real"] is None
    assert any("2026-09" in w for w in warnings)


def test_restate_is_idempotent():
    months = ["2026-01"]; series = [fact(100)]
    once, _ = restatement.restate_series(series, months, IPC, base_month="2026-01")
    twice, _ = restatement.restate_series(once, months, IPC, base_month="2026-01")
    assert twice[0]["transforms"] == ["restated"]   # not doubled


def test_restate_forecast_month_uses_projected_inflation():
    # Apr absent from IPC; project from last actual (Mar=121) at 5%/mo
    months = ["2026-03", "2026-04"]; series = [fact(100), fact(100)]
    out, w = restatement.restate_series(series, months, IPC, base_month="2026-03",
                                        projected_inflation=0.05, last_actual_month="2026-03")
    assert out[0]["real"] == 100.0
    # Apr projected index = 121*1.05 = 127.05; coef = 121/127.05; real = 100*coef ≈ 95.24
    assert abs(out[1]["real"] - (100 * 121 / (121 * 1.05))) < 1e-6
    assert "projected" in out[1]["transforms"]


def test_restate_fin_sets_basemonth_and_real(sample_financials_v2):
    from measures import real_or_nom
    fin = restatement.restate(sample_financials_v2, fin_cfg={})
    assert fin["baseMonth"] is not None                       # closing month of the window
    v0 = fin["incomeStatement"]["monthly"]["ventas"][0]
    assert v0["real"] is not None                             # Jan restated to cierre
    assert "restated" in v0["transforms"]
    monthly = fin["incomeStatement"]["monthly"]["ventas"]
    annual = fin["incomeStatement"]["annual"]["ventas"]
    # annual real == sum of restated monthly real
    assert abs(annual["real"] - sum(real_or_nom(x) for x in monthly)) < 1e-6


def test_restate_degrades_without_year(sample_parsed):
    # a model whose months don't map to IPC (year stripped) -> all-nominal + warning, no crash
    from financials import build_financials
    sp = dict(sample_parsed); sp["year"] = None
    fin = build_financials(sp)
    fin = restatement.restate(fin, fin_cfg={})
    assert fin["baseMonth"] is None
    assert fin["incomeStatement"]["monthly"]["ventas"][0]["real"] is None
    assert any("nominal" in w.lower() for w in fin["warnings"])
