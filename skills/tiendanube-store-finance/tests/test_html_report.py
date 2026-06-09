from workbook import parse_workbook
from financials import build_financials
from html_report import build_html

def test_build_html_contains_brand_and_statement(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    cfg = {"brand": {"name": "ACME", "accent": "#123456", "currencySymbol": "$"}}
    results = {"ratios": {"gross_margin": 0.5}, "forecast": {}, "variance": {}}
    html = build_html(fin, results, cfg)
    assert "ACME" in html and "Estado de Resultados" in html
    assert "#123456" in html  # accent applied
    assert "supuesto" in html.lower()  # assumption caveat present

def test_build_html_renders_data_warnings(fixture_workbook):
    fin = build_financials(parse_workbook(fixture_workbook))
    fin["warnings"] = ["'utilidad neta' tiene celdas con error (#REF!) en el workbook"]
    html = build_html(fin, {"ratios": {}, "forecast": {}, "variance": {}},
                      {"brand": {"name": "ACME"}})
    assert "Advertencias" in html and "#REF!" in html
