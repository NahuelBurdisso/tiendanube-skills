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
    b = fiscal.ri_bridge(resultado_antes=1000, ventas=5000, compras_gravadas=2000, cfg=cfg)
    assert round(b["iibb"], 2) == 175.0                  # 5000*.035
    assert round(b["ganancias"], 2) == 247.5             # (1000-175)*.30
    assert round(b["resultadoDespues"], 2) == round(1000 - 175 - 247.5, 2)
    assert b["ganancias_nota"].startswith("Estimación")
