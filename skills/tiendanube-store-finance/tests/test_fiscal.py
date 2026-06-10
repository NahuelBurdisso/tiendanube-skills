import importlib.util, pathlib, pytest
def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
fiscal = _load("fiscal")

def test_iva_position_debito_minus_credito():
    pos = fiscal.iva_position(ventas=1000, compras_gravadas=400, alicuota=0.21)
    assert round(pos["debito"], 2) == 210.0
    assert round(pos["credito"], 2) == 84.0
    assert round(pos["posicion"], 2) == 126.0

def test_ri_bridge_estimacion():
    cfg = {"regimen": "responsable_inscripto", "alicuotaIIBB": 0.035,
           "alicuotaEfectivaGanancias": 0.30, "alicuotaIVAVentas": 0.21,
           "proporcionComprasGravadas": 1.0}
    b = fiscal.ri_bridge(resultado_neto=1000, ventas=5000, compras_gravadas=2000, cfg=cfg)
    assert round(b["iibb"], 2) == 175.0                  # 5000*.035 (informativo)
    assert round(b["ganancias"], 2) == 300.0             # 1000*.30 (sobre resultado neto)
    assert round(b["resultadoDespues"], 2) == 700.0      # neto − Ganancias (IIBB NO re-restado)
    assert round(b["resultadoAntes"], 2) == 1000.0
    assert b["ganancias_nota"].startswith("Estimación")
    assert "Verificar" in b["iibb_nota"]

TABLES = {"monotributo": {"resolucion": "test", "categorias": {
    "A": {"techoFacturacionAnual": 1000000, "cuotaMensualTotal": 30000},
    "H": {"techoFacturacionAnual": 9000000, "cuotaMensualTotal": 90000},
    "K": {"techoFacturacionAnual": 30000000, "cuotaMensualTotal": 300000}}}}

def test_monotributo_proximity_uses_nominal():
    r = fiscal.monotributo_status(categoria="H", facturacion_anual_nominal=8500000, tables=TABLES)
    assert r["cuotaMensualTotal"] == 90000
    assert round(r["headroom"], 2) == 500000.0
    assert r["proximidad"] > 0.9

def test_monotributo_over_max_hard_errors():
    with pytest.raises(ValueError):
        fiscal.monotributo_status(categoria="K", facturacion_anual_nominal=31000000, tables=TABLES)


def test_apply_fiscal_adds_block_on_nominal(sample_financials_v2):
    cfg = {"fiscal": {"regimen": "monotributo", "categoriaMonotributo": "H"}}
    fin = fiscal.apply_fiscal(sample_financials_v2, cfg)
    assert fin["fiscal"]["regimen"] == "monotributo"
    assert "cuotaMensualTotal" in fin["fiscal"]["monotributo"]
    # fiscal runs on NOMINAL: no income-statement measure may carry 'restated' yet
    for series in fin["incomeStatement"]["monthly"].values():
        assert all("restated" not in m["transforms"] for m in series)


def test_apply_fiscal_tolerates_missing_config(sample_financials_v2):
    fin = fiscal.apply_fiscal(sample_financials_v2, {})   # no fiscal block
    assert fin["fiscal"]["regimen"] is None               # records plainly, no crash


def test_monotributo_partial_year_no_false_exclusion():
    # Actual accumulated facturación is below the max techo, but the run-rate annualized
    # figure is above it. Must NOT hard-error (a strong quarter isn't an exclusion); the
    # run-rate over the techo surfaces as proximidad > 1 (a lever signal), not a crash.
    from financials import build_financials
    tmax = max(c["techoFacturacionAnual"]
               for c in fiscal.load_fiscal_tables()["monotributo"]["categorias"].values())
    monthly = tmax * 0.15                       # 2 months -> actual 0.30*tmax, annualized 1.8*tmax
    keys = ["ventas","costoReposicion","comisiones","utilidadBruta","costosFijos",
            "amortizacion","utilidadOperativa","gastosVariables","utilidadNeta"]
    mp = {k: [0, 0] for k in keys}; mp["ventas"] = [monthly, monthly]
    parsed = {"months": ["Enero","Febrero"], "year": 2025,
              "incomeStatement": {"monthly": mp},
              "cashFlow": {"monthly": {"ingresos":[0,0],"egresos":[0,0],"total":[0,0]}},
              "breakEven": {"margenBrutoMonthly": [], "facturacionEquilibrioMonthly": []},
              "warnings": []}
    fin = build_financials(parsed)
    fin = fiscal.apply_fiscal(fin, {"fiscal": {"regimen": "monotributo", "categoriaMonotributo": "K"}})
    assert fin["fiscal"]["monotributo"]["proximidad"] > 1   # run-rate over techo, no exclusion raised
