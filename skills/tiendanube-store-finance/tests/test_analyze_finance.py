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
