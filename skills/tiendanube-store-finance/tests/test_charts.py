import importlib.util, pathlib
def _load(name):
    p = pathlib.Path(__file__).parent.parent / "scripts" / f"{name}.py"
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
charts = _load("charts")
M = lambda v: f"${v:,.0f}"

def test_dual_bars_draws_nominal_and_real():
    svg = charts.dual_bars(["E","F","M"], [100,120,140], [100,110,115], "#6B2532", "#B08858", M)
    assert "<svg" in svg and svg.count("<rect") >= 6 + 1   # 2 series x 3 + axis-ish

def test_dual_bars_tolerates_missing_real():
    svg = charts.dual_bars(["E","F"], [100,120], [100, None], "#6B2532", "#B08858", M)
    assert "<svg" in svg   # no crash on None real (IPC gap)

def test_tornado_orders_by_magnitude():
    svg = charts.tornado([("c",200),("a",100),("b",50)], "#6B2532", M)
    assert svg.index(">c<") < svg.index(">a<") < svg.index(">b<")


def test_chart_text_labels_are_escaped():
    out = charts._t(0, 0, '<b>x</b> & "y"')
    assert "<b>" not in out and "&lt;b&gt;" in out and "&amp;" in out
