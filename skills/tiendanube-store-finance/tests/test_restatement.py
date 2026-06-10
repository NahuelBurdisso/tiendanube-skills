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
