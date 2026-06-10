import json, pathlib
from analyze_finance import run

def test_run_produces_all_artifacts(fixture_workbook, tmp_path):
    cfg = {"brand": {"name": "ACME"}, "finance": {"forecastPeriods": 6, "enableDcf": False}}
    cfg_path = tmp_path / "report.config.json"; cfg_path.write_text(json.dumps(cfg))
    out = run(fixture_workbook, str(cfg_path), str(tmp_path))
    assert pathlib.Path(out["financials"]).exists()
    assert pathlib.Path(out["xlsx"]).exists()
    assert pathlib.Path(out["html"]).exists()
    fin = json.loads(pathlib.Path(out["financials"]).read_text())
    assert fin["schemaVersion"] == "2.0"
    assert "ratios" in out["results"]


def test_pipeline_fills_real(fixture_workbook, tmp_path):
    cfg = {"brand": {"name": "ACME"}, "finance": {}}
    cfg_path = tmp_path / "report.config.json"; cfg_path.write_text(json.dumps(cfg))
    out = run(fixture_workbook, str(cfg_path), str(tmp_path))
    fin = json.loads(pathlib.Path(out["financials"]).read_text())
    assert fin["baseMonth"] is not None                       # reexpresión ran
    assert fin["incomeStatement"]["monthly"]["ventas"][0]["real"] is not None


def test_pipeline_order_fiscal_then_restate(fixture_workbook, tmp_path):
    cfg = {"brand": {"name": "ACME"}, "finance": {},
           "fiscal": {"regimen": "monotributo", "categoriaMonotributo": "A"}}
    cfg_path = tmp_path / "report.config.json"; cfg_path.write_text(json.dumps(cfg))
    out = run(fixture_workbook, str(cfg_path), str(tmp_path))
    fin = json.loads(pathlib.Path(out["financials"]).read_text())
    assert "fiscal" in fin and fin["fiscal"]["regimen"] == "monotributo"   # fiscal applied
    assert fin["baseMonth"] is not None                                    # restate ran after


def test_pipeline_emits_levers(fixture_workbook, tmp_path):
    cfg = {"brand": {"name": "ACME"}, "finance": {}}
    cfg_path = tmp_path / "report.config.json"; cfg_path.write_text(json.dumps(cfg))
    out = run(fixture_workbook, str(cfg_path), str(tmp_path))
    lv = out["results"]["levers"]
    assert "levers" in lv and "porDriver" in lv
    assert "totalImpacto" not in lv          # never a grand total


def test_pipeline_runs_gates(fixture_workbook, tmp_path, monkeypatch):
    import gates
    calls = {"n": 0}; real = gates.run_all
    def spy(fin, cfg):
        calls["n"] += 1
        return real(fin, cfg)
    monkeypatch.setattr(gates, "run_all", spy)
    cfg = {"brand": {"name": "A"}, "finance": {},
           "fiscal": {"regimen": "monotributo", "categoriaMonotributo": "A"}}
    cfg_path = tmp_path / "c.json"; cfg_path.write_text(json.dumps(cfg))
    run(fixture_workbook, str(cfg_path), str(tmp_path))
    assert calls["n"] == 1
