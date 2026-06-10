import json
import pathlib

REF = pathlib.Path(__file__).parent.parent / "reference"


def test_ipc_table_shape():
    d = json.loads((REF / "ipc-indec.json").read_text())
    assert d["indice"] == "IPC nivel general"
    assert d["fuente"].startswith("INDEC")
    for k in ("basePeriod", "lastUpdated", "vigenciaHasta"):
        assert k in d
    series = d["serie"]
    keys = sorted(series)
    vals = [series[k] for k in keys]
    assert all(b >= a for a, b in zip(vals, vals[1:]))   # index non-decreasing
    assert all(len(k) == 7 and k[4] == "-" for k in keys)


def test_fiscal_tables_shape():
    d = json.loads((REF / "tablas-fiscales-ar.json").read_text())
    assert "lastUpdated" in d and "vigenciaHasta" in d
    cats = d["monotributo"]["categorias"]
    for c in cats.values():
        assert "techoFacturacionAnual" in c and "cuotaMensualTotal" in c
    techos = [c["techoFacturacionAnual"] for c in cats.values()]
    assert techos == sorted(techos)
    assert "iibbDefaults" in d
