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
