import json, pathlib, pytest
from analyze_finance import run
from measures import nom

CFG = str(pathlib.Path(__file__).parent.parent / "scripts" / "report.config.example.json")
SAMPLES = {
    "acme": pathlib.Path.home() / "Desktop/Projects/acme/reports/deliverables/Acme - Mas Orden Mas Ganancia - Cliente .xlsx",
    "maxikiosco": pathlib.Path.home() / "Desktop/Maxikiosco La Esquina - Reporte 01-2026 a 12-2026.xlsx",
}

def test_golden_acme_full_run(tmp_path):
    wb = SAMPLES["acme"]
    if not wb.exists():
        pytest.skip("Acme sample not present")
    out = run(str(wb), CFG, str(tmp_path))
    fin = json.loads(pathlib.Path(out["financials"]).read_text())
    assert fin["schemaVersion"] == "2.0"
    assert isinstance(fin["warnings"], list)
    # tie-out: nominal annual ventas == Σ monthly (reexpresión/fiscal never break this)
    a = fin["incomeStatement"]["annual"]["ventas"]
    m = fin["incomeStatement"]["monthly"]["ventas"]
    assert abs(nom(a) - sum(nom(x) for x in m)) < 1.0
    assert pathlib.Path(out["xlsx"]).exists() and pathlib.Path(out["html"]).exists()

def test_golden_maxikiosco_fails_clearly(tmp_path):
    # Divergent template (no ESTADO DE RESULTADOS anchor): must fail with a clear
    # diagnostic, never produce a silent/wrong report.
    wb = SAMPLES["maxikiosco"]
    if not wb.exists():
        pytest.skip("Maxikiosco sample not present")
    with pytest.raises(ValueError):
        run(str(wb), CFG, str(tmp_path))
